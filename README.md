# PaddleOCR Deploy HPS

[简体中文](README_cn.md)

High-performance, fully offline, containerized deployment solutions for [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) pipelines.

## Highlights

- **Fully Offline** — All models are pre-downloaded and baked into Docker images at build time. No internet access required at runtime, making it suitable for air-gapped and private network environments.
- **High Performance** — Built on NVIDIA Triton Inference Server with dynamic batching, concurrent request handling, and efficient GPU utilization for production-grade throughput.
- **One-Command Startup** — A single `docker compose up` brings up the entire service stack. No manual model downloads, no environment setup, no dependency conflicts.
- **Production Ready** — Includes FastAPI gateway with concurrency control, health check endpoints (liveness + readiness), structured logging, and graceful error handling.
- **Configurable** — Fine-tune concurrency limits, timeout thresholds, worker count, Triton batching, and instance count via environment variables — no code changes needed.
- **Consistent API** — All pipelines expose a unified REST API following the same request/response conventions, simplifying client integration.

## Pipelines

| Pipeline | Description | Docs |
|----------|-------------|------|
| [PP-OCRv5](PP-OCRv5/) | High-accuracy OCR supporting simplified/traditional Chinese, English, Japanese, pinyin, handwriting, vertical text, and rare characters | [English](PP-OCRv5/README.md) \| [中文](PP-OCRv5/README_cn.md) |
| [PP-StructureV3](PP-StructureV3/) | Document layout parsing with table, formula, seal, and chart recognition, outputting structured Markdown | [English](PP-StructureV3/README.md) \| [中文](PP-StructureV3/README_cn.md) |
| [PaddleOCR-VL](PaddleOCR-VL/) | Vision-language model based document understanding powered by PaddleOCR-VL-1.5 with layout detection | [English](PaddleOCR-VL/README.md) \| [中文](PaddleOCR-VL/README_ch.md) |

## Requirements

- x64 CPU
- NVIDIA GPU, Compute Capability >= 8.0 and < 12.0
- NVIDIA driver supporting CUDA 12.6
- Docker >= 19.03
- Docker Compose >= 2.0

## Quick Start

Choose a pipeline directory and start the services:

```bash
git clone https://github.com/kyle-kw/paddleocr-deploy-hps.git
cd paddleocr-deploy-hps

# Example: start PP-OCRv5
cd PP-OCRv5
docker compose up
```

Refer to each pipeline's README for detailed configuration and API usage.

## License

This project is licensed under the [MIT License](LICENSE).
