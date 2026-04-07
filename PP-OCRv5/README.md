# PP-OCRv5 High-Performance Service Deployment

[简体中文](README_cn.md)

This directory provides a high-performance service deployment solution for PP-OCRv5 with concurrent request processing support.

> This solution currently only supports NVIDIA GPUs. Support for other inference devices is still being developed.

## Architecture

```
Client → FastAPI Gateway → Triton Server
```

| Component       | Description                                                        |
|-----------------|--------------------------------------------------------------------|
| FastAPI Gateway | Unified access point, simplified client calls, concurrency control |
| Triton Server   | OCR models and pipeline orchestration; model management, dynamic batching, inference scheduling |

## Requirements

- x64 CPU
- NVIDIA GPU, Compute Capability >= 8.0 and < 12.0
- NVIDIA driver supporting CUDA 12.6
- Docker >= 19.03
- Docker Compose >= 2.0

## Quick Start

1. Clone the repository and navigate to this directory:

```bash
git clone https://github.com/kyle-kw/paddleocr-deploy-hps.git
cd paddleocr-deploy-hps/PP-OCRv5
```

2. Start the services:

```bash
docker compose up
```

The above command will start 2 containers in sequence:

| Service | Description | Port |
|---------|-------------|------|
| `paddleocr-ocrv5` | Triton inference server | 8000 (internal) |
| `paddleocr-ocrv5-gateway` | FastAPI gateway (external entry point) | 8080 |

> The first startup will automatically download and build images, which takes longer. Subsequent startups will use local images and start faster.

## Configuration

### Environment Variables

You can configure the services by setting environment variables in the `compose.yml` file or by passing them directly. For example:

```bash
export HPS_MAX_CONCURRENT_REQUESTS=8
```

| Variable | Default | Description |
|----------|---------|-------------|
| `HPS_MAX_CONCURRENT_REQUESTS` | 16 | Max concurrent requests forwarded to Triton |
| `HPS_INFERENCE_TIMEOUT` | 600 | Request timeout in seconds |
| `HPS_HEALTH_CHECK_TIMEOUT` | 5 | Health check timeout in seconds |
| `HPS_LOG_LEVEL` | INFO | Log level (DEBUG, INFO, WARNING, ERROR) |
| `HPS_FILTER_HEALTH_ACCESS_LOG` | true | Whether to filter health check access logs |
| `UVICORN_WORKERS` | 4 | Number of gateway worker processes |
| `DEVICE_ID` | 0 | Inference device ID to use |
| `GATEWAY_PORT` | 8080 | Host port mapped to gateway |

### Pipeline Configuration

To adjust pipeline configurations (such as model path, batch size, deployment device, etc.), please refer to the Pipeline Configuration section in the [PP-OCRv5 Usage Tutorial](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/OCR.en.md).

## API Usage

### OCR

**Endpoint:** `POST /ocr`

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | string | Yes | - | Base64-encoded file content or accessible URL |
| `fileType` | integer | No | Auto-detect | 0 for PDF, 1 for image |
| `useDocOrientationClassify` | boolean | No | false | Auto-correct 0/90/180/270 degree rotations |
| `useDocUnwarping` | boolean | No | false | Correct distorted/skewed images |
| `useTextlineOrientation` | boolean | No | false | Correct 0/180 degree text line angles |
| `textDetLimitSideLen` | integer | No | 64 | Image dimension constraint |
| `textDetLimitType` | string | No | "min" | Constraint type ("min" or "max") |
| `textDetThresh` | number | No | 0.3 | Text detection pixel threshold |
| `textDetBoxThresh` | number | No | 0.6 | Detection box confidence threshold |
| `textDetUnclipRatio` | number | No | 1.5 | Text region expansion coefficient |
| `textRecScoreThresh` | number | No | 0.0 | Recognition confidence minimum |
| `visualize` | boolean | No | null | Return annotated result images |

**Example:**

```bash
curl -X POST http://localhost:8080/ocr \
  -H "Content-Type: application/json" \
  -d '{
    "file": "<base64_encoded_image>",
    "fileType": 1
  }'
```

**Response:**

```json
{
  "logId": "xxx",
  "errorCode": 0,
  "errorMsg": "Success",
  "result": {
    "ocrResults": [
      {
        "prunedResult": {},
        "ocrImage": "<base64>",
        "inputImage": "<base64>"
      }
    ],
    "dataInfo": {}
  }
}
```

For the full API specification, please refer to the [Official API Documentation](https://ai.baidu.com/ai-doc/AISTUDIO/Kmfl2ycs0).

### Health Checks

```bash
# Liveness check
curl http://localhost:8080/health

# Readiness check (verifies Triton service is ready to process requests)
curl http://localhost:8080/health/ready
```

## Performance Tuning

### Concurrency Settings

The gateway uses a semaphore to control concurrency for requests forwarded to Triton:

- **`HPS_MAX_CONCURRENT_REQUESTS`** (default 16): Controls the max number of concurrent requests sent to Triton
  - Too low (4): Underutilized inference device, requests queue unnecessarily
  - Too high (64): May overload Triton, causing OOM or timeouts
  - Default value of 16 allows enough requests to queue for the next batch while the current batch is being processed
  - If inference device resources are limited, consider lowering this value

**High-throughput configuration example:**

```bash
HPS_MAX_CONCURRENT_REQUESTS=32
UVICORN_WORKERS=8
```

**Low-latency configuration example:**

```bash
HPS_MAX_CONCURRENT_REQUESTS=8
HPS_INFERENCE_TIMEOUT=300
UVICORN_WORKERS=2
```

### Worker Processes

Each Uvicorn worker is an independent process with its own event loop:

- **1 worker**: Simple, but limited to a single process
- **4 workers**: Suitable for most scenarios
- **8+ workers**: Suitable for high-concurrency scenarios with many small requests

### Triton Dynamic Batching

Triton automatically batches requests to improve inference device utilization. The maximum batch size is controlled by the `max_batch_size` parameter in the model configuration file (default: 8), located at `config.pbtxt` under each model directory in the model repository.

### Triton Instance Count

The number of parallel inference instances for each Triton model is configured via the `instance_group` section in `config.pbtxt` (default: 1). Increasing the instance count improves parallelism but consumes more device resources.

```
instance_group [
  {
      count: 1       # Number of instances; increase for higher parallelism
      kind: KIND_GPU
      gpus: [ 0 ]
  }
]
```

There is a trade-off between instance count and dynamic batching:

- **Single instance (`count: 1`)**: Dynamic batching combines multiple requests into one batch for parallel execution, but all requests in the same batch must wait for the slowest one to finish before results are returned. A single instance can only process one batch at a time. Best suited for scenarios with limited GPU memory or uniform request processing times
- **Multiple instances (`count: 2+`)**: Multiple instances can process different batches simultaneously, reducing queuing time and improving latency. Each additional instance consumes extra GPU memory. Adjust based on available resources

## Troubleshooting

### Service Fails to Start

Check the logs for each service to identify the issue:

```bash
docker compose logs paddleocr-ocrv5
docker compose logs paddleocr-ocrv5-gateway
```

Common causes include port conflicts, unavailable inference devices, or image pull failures.

### Timeout Errors

- Increase `HPS_INFERENCE_TIMEOUT` (for complex documents)
- If the inference device is overloaded, reduce `HPS_MAX_CONCURRENT_REQUESTS`

### Out of Memory

- Reduce `HPS_MAX_CONCURRENT_REQUESTS`
- Ensure only one service runs per inference device
- Check `shm_size` in compose.yml (default: 4GB)
