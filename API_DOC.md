# PaddleOCR Deploy HPS API 接口文档

本文档描述了三个产线服务的 REST API 接口规范。所有接口均使用 JSON 格式进行请求和响应。

---

## 目录

- [PaddleOCR Deploy HPS API 接口文档](#paddleocr-deploy-hps-api-接口文档)
  - [目录](#目录)
  - [1. PP-OCRv6 - OCR 识别接口](#1-pp-ocrv6---ocr-识别接口)
    - [基本信息](#基本信息)
    - [请求参数](#请求参数)
    - [请求示例](#请求示例)
    - [成功响应](#成功响应)
    - [错误响应](#错误响应)
  - [2. PP-StructureV3 - 文档版面解析接口](#2-pp-structurev3---文档版面解析接口)
    - [基本信息](#基本信息-1)
    - [请求参数](#请求参数-1)
    - [请求示例](#请求示例-1)
    - [成功响应](#成功响应-1)
    - [错误响应](#错误响应-1)
  - [3. PaddleOCR-VL - 视觉语言模型版面解析接口](#3-paddleocr-vl---视觉语言模型版面解析接口)
    - [基本信息](#基本信息-2)
    - [请求参数](#请求参数-2)
    - [请求示例](#请求示例-2)
    - [成功响应](#成功响应-2)
    - [错误响应](#错误响应-2)
  - [通用说明](#通用说明)
    - [file 参数](#file-参数)
    - [fileType 参数](#filetype-参数)
    - [统一响应格式](#统一响应格式)
  - [健康检查接口](#健康检查接口)
    - [存活检查](#存活检查)
    - [就绪检查](#就绪检查)
    - [各服务默认端口](#各服务默认端口)

---

## 1. PP-OCRv6 - OCR 识别接口

高精度 OCR 识别，支持简体/繁体中文、英文、日文、拼音、手写体、竖排文本和生僻字。

### 基本信息

| 项目 | 说明 |
|------|------|
| 请求地址 | `POST /ocr` |
| 默认端口 | 8080 |
| Content-Type | application/json |
| 响应格式 | JSON |

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| `file` | string | **是** | - | 图像或 PDF 文件的 Base64 编码内容，或可访问的 URL |
| `fileType` | integer \| null | 否 | 自动推断 | 文件类型：`0` = PDF，`1` = 图像 |
| `useDocOrientationClassify` | boolean \| null | 否 | false | 是否自动矫正 0/90/180/270 度旋转 |
| `useDocUnwarping` | boolean \| null | 否 | false | 是否矫正扭曲/倾斜图片 |
| `useTextlineOrientation` | boolean \| null | 否 | false | 是否矫正文本行 0/180 度方向 |
| `textDetLimitSideLen` | integer \| null | 否 | 64 | 文本检测的图像边长限制（大于 0） |
| `textDetLimitType` | string \| null | 否 | "min" | 边长限制类型：`"min"` 或 `"max"` |
| `textDetThresh` | number \| null | 否 | 0.3 | 文本检测像素阈值（范围 0-1） |
| `textDetBoxThresh` | number \| null | 否 | 0.6 | 文本检测框置信度阈值（范围 0-1） |
| `textDetUnclipRatio` | number \| null | 否 | 1.5 | 文本区域扩张系数（大于 0） |
| `textRecScoreThresh` | number \| null | 否 | 0.0 | 文本识别置信度最低阈值（范围 0-1） |
| `visualize` | boolean \| null | 否 | null | 是否返回带标注的可视化结果图 |

### 请求示例

```bash
curl -X POST http://localhost:8080/ocr \
  -H "Content-Type: application/json" \
  -d '{
    "file": "<base64_encoded_image>",
    "fileType": 1
  }'
```

**Python 示例：**

```python
import base64
import requests

API_URL = "http://localhost:8080/ocr"

with open("image.jpg", "rb") as f:
    file_data = base64.b64encode(f.read()).decode("ascii")

payload = {
    "file": file_data,
    "fileType": 1,
    "useDocOrientationClassify": False,
    "visualize": True
}

response = requests.post(API_URL, json=payload)
result = response.json()
```

### 成功响应

**HTTP 状态码：** `200`

```json
{
  "logId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "errorCode": 0,
  "errorMsg": "Success",
  "result": {
    "ocrResults": [
      {
        "prunedResult": {},
        "ocrImage": "<base64>",
        "docPreprocessingImage": "<base64>",
        "inputImage": "<base64>"
      }
    ],
    "dataInfo": {}
  }
}
```

**响应参数说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `logId` | string | 请求唯一标识 UUID |
| `errorCode` | integer | 错误码，成功时为 `0` |
| `errorMsg` | string | 错误信息，成功时为 `"Success"` |
| `result` | object | 结果对象 |
| `result.ocrResults` | array | OCR 识别结果数组，每个元素对应一页 |
| `result.ocrResults[].prunedResult` | object | 简化的识别结果，包含文本坐标、内容及置信度 |
| `result.ocrResults[].ocrImage` | string \| null | 标注文本位置的 JPEG 图像（Base64 编码），仅当 `visualize=true` 时返回 |
| `result.ocrResults[].docPreprocessingImage` | string \| null | 预处理可视化图像（Base64 编码） |
| `result.ocrResults[].inputImage` | string \| null | 输入原始图像（Base64 编码） |
| `result.dataInfo` | object | 输入数据的元信息 |

### 错误响应

**HTTP 状态码：** 非 `200`

```json
{
  "logId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "errorCode": 400,
  "errorMsg": "错误描述信息"
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `logId` | string | 请求唯一标识 UUID |
| `errorCode` | integer | 错误码，与 HTTP 状态码一致 |
| `errorMsg` | string | 错误描述 |

---

## 2. PP-StructureV3 - 文档版面解析接口

文档版面解析，支持表格、公式、印章、图表识别，输出结构化 Markdown。

### 基本信息

| 项目 | 说明 |
|------|------|
| 请求地址 | `POST /layout-parsing` |
| 默认端口 | 8081 |
| Content-Type | application/json |
| 响应格式 | JSON |

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| `file` | string | **是** | - | 图像或 PDF 文件的 Base64 编码内容，或可访问的 URL |
| `fileType` | integer \| null | 否 | 自动推断 | 文件类型：`0` = PDF，`1` = 图像 |
| `useDocOrientationClassify` | boolean \| null | 否 | false | 是否自动矫正 0/90/180/270 度旋转 |
| `useDocUnwarping` | boolean \| null | 否 | false | 是否矫正扭曲/倾斜图片 |
| `useTextlineOrientation` | boolean \| null | 否 | false | 是否矫正文本行 0/180 度方向 |
| `useSealRecognition` | boolean \| null | 否 | false | 是否启用印章文本识别 |
| `useTableRecognition` | boolean \| null | 否 | true | 是否启用表格识别（转 HTML/Markdown） |
| `useFormulaRecognition` | boolean \| null | 否 | true | 是否启用公式识别（转 LaTeX） |
| `useChartRecognition` | boolean \| null | 否 | false | 是否启用图表解析（转表格） |
| `useRegionDetection` | boolean \| null | 否 | true | 是否启用增强版面区域检测 |
| `layoutThreshold` | number \| null | 否 | 0.5 | 版面区域检测得分阈值（范围 0-1） |
| `textDetLimitSideLen` | integer \| null | 否 | 736 | 文本检测的图像边长限制 |
| `textDetThresh` | number \| null | 否 | 0.3 | 文本检测像素阈值 |
| `textDetBoxThresh` | number \| null | 否 | 0.6 | 文本检测框阈值 |
| `textRecScoreThresh` | number \| null | 否 | 0.0 | 文本识别置信度阈值 |
| `visualize` | boolean \| null | 否 | null | 是否返回可视化结果图像 |

### 请求示例

```bash
curl -X POST http://localhost:8081/layout-parsing \
  -H "Content-Type: application/json" \
  -d '{
    "file": "<base64_encoded_image>",
    "fileType": 1
  }'
```

**Python 示例：**

```python
import base64
import requests

API_URL = "http://localhost:8081/layout-parsing"

with open("document.pdf", "rb") as f:
    file_data = base64.b64encode(f.read()).decode("ascii")

payload = {
    "file": file_data,
    "fileType": 0,
    "useTableRecognition": True,
    "useFormulaRecognition": True
}

response = requests.post(API_URL, json=payload)
result = response.json()
```

### 成功响应

**HTTP 状态码：** `200`

```json
{
  "logId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "errorCode": 0,
  "errorMsg": "Success",
  "result": {
    "layoutParsingResults": [
      {
        "prunedResult": {},
        "markdown": {
          "text": "# 文档标题\n\n正文内容...",
          "images": {
            "image_0.jpg": "<base64>"
          }
        },
        "outputImages": {
          "layout": "<base64>"
        },
        "inputImage": "<base64>"
      }
    ],
    "dataInfo": {}
  }
}
```

**响应参数说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `logId` | string | 请求唯一标识 UUID |
| `errorCode` | integer | 错误码，成功时为 `0` |
| `errorMsg` | string | 错误信息，成功时为 `"Success"` |
| `result` | object | 结果对象 |
| `result.layoutParsingResults` | array | 版面解析结果数组，每个元素对应一页 |
| `result.layoutParsingResults[].prunedResult` | object | 简化的预测结果 |
| `result.layoutParsingResults[].markdown` | object | Markdown 格式输出 |
| `result.layoutParsingResults[].markdown.text` | string | 解析后的 Markdown 文本 |
| `result.layoutParsingResults[].markdown.images` | object | 图片键值对：相对路径 -> Base64 编码 |
| `result.layoutParsingResults[].outputImages` | object | 可视化输出图像（JPEG/Base64），仅当 `visualize=true` 时返回 |
| `result.layoutParsingResults[].inputImage` | string \| null | 输入原始图像（Base64 编码） |
| `result.dataInfo` | object | 输入数据的元信息 |

### 错误响应

**HTTP 状态码：** 非 `200`

```json
{
  "logId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "errorCode": 400,
  "errorMsg": "错误描述信息"
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `logId` | string | 请求唯一标识 UUID |
| `errorCode` | integer | 错误码，与 HTTP 状态码一致 |
| `errorMsg` | string | 错误描述 |

---

## 3. PaddleOCR-VL - 视觉语言模型版面解析接口

基于 PaddleOCR-VL-1.6 视觉语言模型的文档理解，结合版面检测，支持多页重构。

### 基本信息

| 项目 | 说明 |
|------|------|
| 请求地址 | `POST /layout-parsing` |
| 默认端口 | 8080 |
| Content-Type | application/json |
| 响应格式 | JSON |

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|:----:|--------|------|
| `file` | string | **是** | - | 图像或 PDF 文件的 Base64 编码内容，或可访问的 URL |
| `fileType` | integer \| null | 否 | 自动推断 | 文件类型：`0` = PDF，`1` = 图像 |
| `useDocOrientationClassify` | boolean \| null | 否 | false | 是否自动矫正 0/90/180/270 度旋转 |
| `useDocUnwarping` | boolean \| null | 否 | false | 是否矫正扭曲/倾斜图片 |
| `useLayoutDetection` | boolean \| null | 否 | true | 是否启用版面区域检测与排序 |
| `useChartRecognition` | boolean \| null | 否 | false | 是否启用图表转表格 |
| `layoutThreshold` | number \| null | 否 | 0.5 | 版面模型置信度阈值（范围 0-1） |
| `layoutNms` | boolean \| null | 否 | false | 是否应用 NMS 后处理去除重叠框 |
| `layoutUnclipRatio` | number \| null | 否 | 1.0 | 检测框扩张系数 |
| `promptLabel` | string \| null | 否 | null | VL 模型提示类型：`"ocr"`、`"formula"`、`"table"` 或 `"chart"` |
| `visualize` | boolean \| null | 否 | null | 是否返回可视化图像和中间结果 |
| `prettifyMarkdown` | boolean \| null | 否 | false | 是否输出格式化的 Markdown |
| `mergeTables` | boolean \| null | 否 | true | 是否合并跨页表格 |
| `relevelTitles` | boolean \| null | 否 | true | 是否重新识别标题层级 |
| `maxPixels` | number \| null | 否 | null | 最大图像尺寸（内存受限时可调低） |

### 请求示例

```bash
curl -X POST http://localhost:8080/layout-parsing \
  -H "Content-Type: application/json" \
  -d '{
    "file": "<base64_encoded_image>",
    "fileType": 1
  }'
```

**Python 示例：**

```python
import base64
import requests

API_URL = "http://localhost:8080/layout-parsing"

with open("document.pdf", "rb") as f:
    file_data = base64.b64encode(f.read()).decode("ascii")

payload = {
    "file": file_data,
    "fileType": 0,
    "useLayoutDetection": True,
    "prettifyMarkdown": True
}

response = requests.post(API_URL, json=payload)
result = response.json()
```

### 成功响应

**HTTP 状态码：** `200`

```json
{
  "logId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "errorCode": 0,
  "errorMsg": "Success",
  "result": {
    "layoutParsingResults": [
      {
        "prunedResult": {},
        "markdown": {
          "text": "# 文档标题\n\n正文内容...",
          "images": {
            "image_0.jpg": "<base64>"
          }
        },
        "outputImages": {
          "layout": "<base64>"
        },
        "inputImage": "<base64>"
      }
    ],
    "dataInfo": {}
  }
}
```

**响应参数说明：**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `logId` | string | 请求唯一标识 UUID |
| `errorCode` | integer | 错误码，成功时为 `0` |
| `errorMsg` | string | 错误信息，成功时为 `"Success"` |
| `result` | object | 结果对象 |
| `result.layoutParsingResults` | array | 版面解析结果数组，每个元素对应一页 |
| `result.layoutParsingResults[].prunedResult` | object | 简化的预测结果 |
| `result.layoutParsingResults[].markdown` | object | Markdown 格式输出 |
| `result.layoutParsingResults[].markdown.text` | string | 解析后的 Markdown 文本 |
| `result.layoutParsingResults[].markdown.images` | object | 图片键值对：相对路径 -> Base64 编码 |
| `result.layoutParsingResults[].outputImages` | object | 可视化输出图像（JPEG/Base64），仅当 `visualize=true` 时返回 |
| `result.layoutParsingResults[].inputImage` | string \| null | 输入原始图像（Base64 编码） |
| `result.dataInfo` | object | 输入数据的元信息 |

### 错误响应

**HTTP 状态码：** 非 `200`

```json
{
  "logId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "errorCode": 400,
  "errorMsg": "错误描述信息"
}
```

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `logId` | string | 请求唯一标识 UUID |
| `errorCode` | integer | 错误码，与 HTTP 状态码一致 |
| `errorMsg` | string | 错误描述 |

---

## 通用说明

### file 参数

所有接口的 `file` 参数支持两种输入方式：

1. **Base64 编码** — 将文件内容进行 Base64 编码后传入
2. **URL** — 传入可访问的文件 URL，服务端会自动下载

### fileType 参数

- `0` — PDF 文件
- `1` — 图像文件（支持 JPG、PNG、BMP、TIFF 等常见格式）
- 不传或传 `null` — 自动根据文件内容推断类型

### 统一响应格式

所有接口遵循统一的响应格式：

```json
{
  "logId": "string",
  "errorCode": 0,
  "errorMsg": "string",
  "result": {}
}
```

- `errorCode` 为 `0` 表示成功，非 `0` 表示错误
- `logId` 可用于日志追踪和问题排查

---

## 健康检查接口

所有产线服务均提供以下健康检查端点：

### 存活检查

```
GET /health
```

返回服务是否运行中。

**响应示例：**

```json
{
  "status": "ok"
}
```

### 就绪检查

```
GET /health/ready
```

返回服务是否已就绪（验证 Triton 推理服务是否可以处理请求）。

**响应示例：**

```json
{
  "status": "ok"
}
```

### 各服务默认端口

| 产线 | 默认端口 |
|------|----------|
| PP-OCRv6 | 8080 |
| PP-StructureV3 | 8081 |
| PaddleOCR-VL | 8080 |

> **注意：** PP-OCRv6 和 PaddleOCR-VL 默认端口相同（8080），请勿同时在同一主机上使用默认配置启动两个服务。可通过环境变量 `GATEWAY_PORT` 修改端口。
