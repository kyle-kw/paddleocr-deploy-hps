# PaddleOCR Deploy HPS

[English](README.md)

基于 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 产线的高性能、完全离线、容器化部署方案。

## 特性

- **完全离线** — 所有模型在构建镜像时预下载并打包，运行时无需联网，适用于内网隔离和私有化部署环境。
- **高性能** — 基于 NVIDIA Triton 推理服务器，支持动态批处理、并发请求处理和高效 GPU 利用，满足生产级吞吐需求。
- **一键启动** — 仅需 `docker compose up` 即可拉起完整服务栈，无需手动下载模型、配置环境或处理依赖冲突。
- **生产就绪** — 内置 FastAPI 网关，提供并发控制、健康检查端点（存活 + 就绪）、结构化日志和优雅的错误处理。
- **灵活配置** — 通过环境变量即可调整并发限制、超时阈值、Worker 数量、Triton 批处理和实例数，无需修改代码。
- **统一接口** — 所有产线遵循相同的 REST API 请求/响应规范，简化客户端集成。

## 产线

| 产线 | 说明 | 文档 |
|------|------|------|
| [PP-OCRv5](PP-OCRv5/) | 高精度 OCR，支持简体/繁体中文、英文、日文、拼音、手写体、竖排文本和生僻字 | [English](PP-OCRv5/README.md) \| [中文](PP-OCRv5/README_cn.md) |
| [PP-StructureV3](PP-StructureV3/) | 文档版面解析，支持表格、公式、印章、图表识别，输出结构化 Markdown | [English](PP-StructureV3/README.md) \| [中文](PP-StructureV3/README_cn.md) |
| [PaddleOCR-VL](PaddleOCR-VL/) | 基于 PaddleOCR-VL-1.5 视觉语言模型的文档理解，结合版面检测 | [English](PaddleOCR-VL/README.md) \| [中文](PaddleOCR-VL/README_ch.md) |

## 环境要求

- x64 CPU
- NVIDIA GPU，Compute Capability >= 8.0 且 < 12.0
- NVIDIA 驱动支持 CUDA 12.6
- Docker >= 19.03
- Docker Compose >= 2.0

## 快速开始

选择一个产线目录并启动服务：

```bash
git clone https://github.com/kyle-kw/paddleocr-deploy-hps.git
cd paddleocr-deploy-hps

# 示例：启动 PP-OCRv5
cd PP-OCRv5
docker compose up
```

详细配置和 API 使用说明请参考各产线的 README 文档。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。
