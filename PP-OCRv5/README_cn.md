# PP-OCRv5 高性能服务化部署

[English](README.md)

本目录提供一套支持并发请求处理的 PP-OCRv5 高性能服务化部署方案。

> 本方案目前暂时只支持 NVIDIA GPU，对其他推理设备的支持仍在完善中。

## 架构

```
客户端 → FastAPI 网关 → Triton 服务器
```

| 组件           | 说明                                   |
|----------------|----------------------------------------|
| FastAPI 网关   | 统一访问入口、简化客户端调用、并发控制 |
| Triton 服务器  | OCR 模型及产线串联逻辑，负责模型管理、动态批处理、推理调度 |

## 环境要求

- x64 CPU
- NVIDIA GPU，Compute Capability >= 8.0 且 < 12.0
- NVIDIA 驱动支持 CUDA 12.6
- Docker >= 19.03
- Docker Compose >= 2.0

## 快速开始

1. 拉取源码并切换到当前目录：

```bash
git clone https://github.com/kyle-kw/paddleocr-deploy-hps.git
cd paddleocr-deploy-hps/PP-OCRv5
```

2. 启动服务：

```bash
docker compose up
```

上述命令将依次启动 2 个容器：

| 服务 | 说明 | 端口 |
|------|------|------|
| `paddleocr-ocrv5` | Triton 推理服务器 | 8000（内部） |
| `paddleocr-ocrv5-gateway` | FastAPI 网关（对外入口） | 8080 |

> 首次启动会自动下载并构建镜像，耗时较长；从第二次启动起将直接使用本地镜像，启动速度更快。

## 配置说明

### 环境变量

可以在 `compose.yml` 文件中设置环境变量，也可以直接设置环境变量，如：

```bash
export HPS_MAX_CONCURRENT_REQUESTS=8
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HPS_MAX_CONCURRENT_REQUESTS` | 16 | 转发到 Triton 的最大并发请求数 |
| `HPS_INFERENCE_TIMEOUT` | 600 | 请求超时时间（秒） |
| `HPS_HEALTH_CHECK_TIMEOUT` | 5 | 健康检查超时时间（秒） |
| `HPS_LOG_LEVEL` | INFO | 日志级别（DEBUG, INFO, WARNING, ERROR） |
| `HPS_FILTER_HEALTH_ACCESS_LOG` | true | 是否过滤健康检查的访问日志 |
| `UVICORN_WORKERS` | 4 | 网关 Worker 进程数 |
| `DEVICE_ID` | 0 | 使用的推理设备 ID |
| `GATEWAY_PORT` | 8080 | 网关映射到宿主机的端口 |

### 产线配置调整

如需调整产线相关配置（如模型路径、批处理大小、部署设备等），请参考 [PP-OCRv5 使用教程](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/OCR.md) 中的产线配置调整说明章节。

## API 使用

### OCR 识别

**接口：** `POST /ocr`

**请求参数：**

| 参数 | 类型 | 是否必填 | 默认值 | 说明 |
|------|------|----------|--------|------|
| `file` | string | 是 | - | Base64 编码的文件内容或可访问的 URL |
| `fileType` | integer | 否 | 自动检测 | 0 表示 PDF，1 表示图片 |
| `useDocOrientationClassify` | boolean | 否 | false | 自动校正 0/90/180/270 度旋转 |
| `useDocUnwarping` | boolean | 否 | false | 校正扭曲/倾斜的图片 |
| `useTextlineOrientation` | boolean | 否 | false | 校正 0/180 度文本行角度 |
| `textDetLimitSideLen` | integer | 否 | 64 | 图片尺寸约束 |
| `textDetLimitType` | string | 否 | "min" | 约束类型（"min" 或 "max"） |
| `textDetThresh` | number | 否 | 0.3 | 文本检测像素阈值 |
| `textDetBoxThresh` | number | 否 | 0.6 | 检测框置信度阈值 |
| `textDetUnclipRatio` | number | 否 | 1.5 | 文本区域扩展系数 |
| `textRecScoreThresh` | number | 否 | 0.0 | 识别置信度最低阈值 |
| `visualize` | boolean | 否 | null | 是否返回标注结果图 |

**示例：**

```bash
curl -X POST http://localhost:8080/ocr \
  -H "Content-Type: application/json" \
  -d '{
    "file": "<base64_encoded_image>",
    "fileType": 1
  }'
```

**响应：**

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

完整接口规范请参考 [官方接口文档](https://ai.baidu.com/ai-doc/AISTUDIO/Kmfl2ycs0)。

### 健康检查

```bash
# 存活检查
curl http://localhost:8080/health

# 就绪检查（验证 Triton 服务是否已准备好处理请求）
curl http://localhost:8080/health/ready
```

## 性能调优

### 并发设置

网关通过信号量控制转发到 Triton 的请求并发数：

- **`HPS_MAX_CONCURRENT_REQUESTS`**（默认 16）：控制发送到 Triton 的最大并发请求数
  - 过低（4）：推理设备利用率不足，请求不必要地排队
  - 过高（64）：可能导致 Triton 过载，出现 OOM 或超时
  - 默认值 16 允许在当前批次处理时有足够请求排队形成下一批次
  - 如推理设备资源有限，建议适当降低此值

**高吞吐配置示例：**

```bash
HPS_MAX_CONCURRENT_REQUESTS=32
UVICORN_WORKERS=8
```

**低延迟配置示例：**

```bash
HPS_MAX_CONCURRENT_REQUESTS=8
HPS_INFERENCE_TIMEOUT=300
UVICORN_WORKERS=2
```

### Worker 进程数

每个 Uvicorn Worker 是独立的进程，有自己的事件循环：

- **1 个 Worker**：简单，但受限于单进程
- **4 个 Worker**：适合大多数场景
- **8+ 个 Worker**：适用于高并发、大量小请求的场景

### Triton 动态批处理

Triton 自动将请求批处理以提高推理设备利用率。最大批处理大小通过模型配置文件中的 `max_batch_size` 参数控制（默认：8），配置文件位于模型仓库目录下的 `config.pbtxt`。

### Triton 实例数

每个 Triton 模型的并行推理实例数通过 `config.pbtxt` 中的 `instance_group` 配置（默认：1）。增加实例数可以提高并行处理能力，但会占用更多设备资源。

```
instance_group [
  {
      count: 1       # 实例数，增大可提高并行度
      kind: KIND_GPU
      gpus: [ 0 ]
  }
]
```

实例数与动态批处理之间存在权衡：

- **单实例（`count: 1`）**：动态批处理会将多个请求合并为一个批次并行执行，但同批次的请求需等待最慢的那个完成后才能一起返回，可能导致部分请求的时延升高。同时，单实例同一时刻只能处理一个批次，当前批次未完成时后续请求只能排队等待。适合显存有限或请求耗时较均匀的场景
- **多实例（`count: 2+`）**：多个实例可以同时各自处理不同的批次，减少排队等待时间，单个请求的时延也会有所改善。但每增加一个实例会额外占用一份模型的显存，需根据推理设备的资源情况酌情设置

## 故障排查与解决

### 服务无法启动

查看各服务的日志以定位问题：

```bash
docker compose logs paddleocr-ocrv5
docker compose logs paddleocr-ocrv5-gateway
```

常见原因包括端口被占用、推理设备不可用或镜像拉取失败。

### 超时错误

- 增加 `HPS_INFERENCE_TIMEOUT`（针对复杂文档）
- 如果推理设备过载，减少 `HPS_MAX_CONCURRENT_REQUESTS`

### 内存/显存不足

- 减少 `HPS_MAX_CONCURRENT_REQUESTS`
- 确保每个推理设备只运行一个服务
- 检查 compose.yml 中的 `shm_size`（默认：4GB）
