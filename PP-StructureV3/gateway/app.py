#!/usr/bin/env python

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

import fastapi
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from paddlex.inference.serving.infra.models import AIStudioNoResultResponse
from paddlex.inference.serving.infra.utils import generate_log_id
from paddlex_hps_client import triton_request_async
from tritonclient.grpc import aio as triton_grpc_aio

TRITON_URL = os.getenv("HPS_TRITON_URL", "paddleocr-structure-v3:8001")
MAX_CONCURRENT_REQUESTS = int(os.getenv("HPS_MAX_CONCURRENT_REQUESTS", "16"))
INFERENCE_TIMEOUT = int(os.getenv("HPS_INFERENCE_TIMEOUT", "600"))
LOG_LEVEL = os.getenv("HPS_LOG_LEVEL", "INFO")
HEALTH_CHECK_TIMEOUT = int(os.getenv("HPS_HEALTH_CHECK_TIMEOUT", "5"))
FILTER_HEALTH_ACCESS_LOG = os.getenv(
    "HPS_FILTER_HEALTH_ACCESS_LOG", "true"
).lower() in ("true", "1", "yes")

TRITON_MODEL_NAME = "layout-parsing"

logger = logging.getLogger(__name__)


def _configure_logger(logger: logging.Logger) -> None:
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


_configure_logger(logger)


def _create_aistudio_output_without_result(
    error_code: int, error_msg: str, *, log_id: Optional[str] = None
) -> dict:
    resp = AIStudioNoResultResponse(
        logId=log_id if log_id is not None else generate_log_id(),
        errorCode=error_code,
        errorMsg=error_msg,
    )
    return resp.model_dump()


@asynccontextmanager
async def _lifespan(app: fastapi.FastAPI):
    logger.info("Initializing PP-StructureV3 gateway...")
    logger.info("Triton URL: %s", TRITON_URL)
    logger.info("Max concurrent requests: %d", MAX_CONCURRENT_REQUESTS)
    logger.info("Inference timeout: %ds", INFERENCE_TIMEOUT)

    app.state.triton_client = triton_grpc_aio.InferenceServerClient(
        url=TRITON_URL,
        keepalive_options=triton_grpc_aio.KeepAliveOptions(
            keepalive_timeout_ms=INFERENCE_TIMEOUT * 1000,
        ),
    )
    app.state.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    logger.info("PP-StructureV3 gateway initialized successfully")
    yield

    logger.info("Shutting down PP-StructureV3 gateway...")
    await app.state.triton_client.close()
    logger.info("PP-StructureV3 gateway shutdown complete")


app = fastapi.FastAPI(
    title="PP-StructureV3 HPS Gateway",
    description="High Performance Server Gateway for PP-StructureV3",
    version="1.0.0",
    lifespan=_lifespan,
)


@app.get("/health", operation_id="checkHealth")
async def health():
    return _create_aistudio_output_without_result(0, "Healthy")


@app.get("/health/ready", operation_id="checkReady")
async def ready(request: Request):
    try:
        client = request.app.state.triton_client

        is_server_ready = await asyncio.wait_for(
            client.is_server_ready(),
            timeout=HEALTH_CHECK_TIMEOUT,
        )
        if not is_server_ready:
            return JSONResponse(
                status_code=503,
                content=_create_aistudio_output_without_result(
                    503, "Triton server not ready"
                ),
            )

        is_model_ready = await asyncio.wait_for(
            client.is_model_ready(TRITON_MODEL_NAME),
            timeout=HEALTH_CHECK_TIMEOUT,
        )
        if not is_model_ready:
            return JSONResponse(
                status_code=503,
                content=_create_aistudio_output_without_result(
                    503, f"Model '{TRITON_MODEL_NAME}' not ready"
                ),
            )

        return _create_aistudio_output_without_result(0, "Ready")
    except asyncio.TimeoutError:
        logger.error("Health check timed out after %ds", HEALTH_CHECK_TIMEOUT)
        return JSONResponse(
            status_code=503,
            content=_create_aistudio_output_without_result(
                503, "Health check timed out"
            ),
        )
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content=_create_aistudio_output_without_result(
                503, f"Service unavailable: {e}"
            ),
        )


@app.post("/layout-parsing", operation_id="infer", response_class=JSONResponse)
async def handle_layout_parsing(request: Request, body: dict):
    """Handle layout-parsing inference request (PP-StructureV3 API)."""
    request_log_id = body.get("logId", generate_log_id())
    logger.info("Processing layout-parsing request %s", request_log_id)

    if "logId" in body:
        logger.debug("Using external logId: %s", request_log_id)
    body["logId"] = request_log_id

    client = request.app.state.triton_client

    try:
        async with request.app.state.semaphore:
            output = await triton_request_async(
                client,
                TRITON_MODEL_NAME,
                body,
                timeout=INFERENCE_TIMEOUT,
            )
    except asyncio.TimeoutError:
        logger.warning("Timeout processing layout-parsing request %s", request_log_id)
        return JSONResponse(
            status_code=504,
            content=_create_aistudio_output_without_result(
                504, "Gateway timeout", log_id=request_log_id
            ),
        )
    except triton_grpc_aio.InferenceServerException as e:
        if "Deadline Exceeded" in str(e):
            logger.warning(
                "Triton timeout for layout-parsing request %s", request_log_id
            )
            return JSONResponse(
                status_code=504,
                content=_create_aistudio_output_without_result(
                    504, "Gateway timeout", log_id=request_log_id
                ),
            )
        logger.error(
            "Triton error for layout-parsing request %s: %s", request_log_id, e
        )
        return JSONResponse(
            status_code=500,
            content=_create_aistudio_output_without_result(
                500, "Internal server error", log_id=request_log_id
            ),
        )
    except Exception:
        logger.exception(
            "Unexpected error for layout-parsing request %s", request_log_id
        )
        return JSONResponse(
            status_code=500,
            content=_create_aistudio_output_without_result(
                500, "Internal server error", log_id=request_log_id
            ),
        )

    if output.get("errorCode", 0) != 0:
        error_code = output.get("errorCode", 500)
        error_msg = output.get("errorMsg", "Unknown error")
        logger.warning(
            "Triton returned error for layout-parsing request %s: %s",
            request_log_id,
            error_msg,
        )
        return JSONResponse(
            status_code=error_code,
            content=_create_aistudio_output_without_result(
                error_code, error_msg, log_id=request_log_id
            ),
        )

    logger.info("Completed layout-parsing request %s", request_log_id)
    return JSONResponse(status_code=200, content=output)


@app.exception_handler(json.JSONDecodeError)
async def _json_decode_exception_handler(request: Request, exc: json.JSONDecodeError):
    logger.warning("Invalid JSON for %s: %s", request.url.path, exc.msg)
    return JSONResponse(
        status_code=400,
        content=_create_aistudio_output_without_result(400, f"Invalid JSON: {exc.msg}"),
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    error_messages = []
    for error in error_details:
        loc = ".".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "Unknown error")
        error_messages.append(f"{loc}: {msg}" if loc else msg)
    error_msg = "; ".join(error_messages)
    logger.warning("Validation error for %s: %s", request.url.path, error_msg)
    return JSONResponse(
        status_code=422,
        content=_create_aistudio_output_without_result(422, error_msg),
    )


@app.exception_handler(asyncio.TimeoutError)
async def _timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
    logger.warning("Request timed out: %s", request.url.path)
    return JSONResponse(
        status_code=504,
        content=_create_aistudio_output_without_result(504, "Gateway timeout"),
    )


@app.exception_handler(Exception)
async def _general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=_create_aistudio_output_without_result(500, "Internal server error"),
    )


class _HealthEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/health" not in record.getMessage()


if FILTER_HEALTH_ACCESS_LOG:
    logging.getLogger("uvicorn.access").addFilter(_HealthEndpointFilter())
