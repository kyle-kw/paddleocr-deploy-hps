# Build args for hardware flexibility
# For CPU-only or non-NVIDIA hardware, override these at build time:
#   docker build --build-arg BASE_IMAGE=<cpu-image> --build-arg DEVICE_TYPE=cpu ...
ARG BASE_IMAGE=ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlex/hps:paddlex3.4-gpu
ARG DEVICE_TYPE=gpu

FROM ${BASE_IMAGE}
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl wget tar \
    && rm -rf /var/lib/apt/lists/*

# Install PaddleX for Python backend models (if not already in base image)
RUN pip install --no-cache-dir paddlex>=3.4.0 || true

# 安装的模型,供离线使用
ENV HOME=/root
RUN mkdir -p "${HOME}/.paddlex/official_models" \
        && cd "${HOME}/.paddlex/official_models" \
        && wget --timeout=120 https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_doc_ori_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_textline_ori_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_server_det_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_server_rec_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/UVDoc_infer.tar \
        && tar -xf PP-LCNet_x1_0_doc_ori_infer.tar \
        && mv PP-LCNet_x1_0_doc_ori_infer PP-LCNet_x1_0_doc_ori \
        && tar -xf PP-LCNet_x1_0_textline_ori_infer.tar \
        && mv PP-LCNet_x1_0_textline_ori_infer PP-LCNet_x1_0_textline_ori \
        && tar -xf PP-OCRv5_server_det_infer.tar \
        && mv PP-OCRv5_server_det_infer PP-OCRv5_server_det \
        && tar -xf PP-OCRv5_server_rec_infer.tar \
        && mv PP-OCRv5_server_rec_infer PP-OCRv5_server_rec \
        && tar -xf UVDoc_infer.tar \
        && mv UVDoc_infer UVDoc \
        && rm -f UVDoc_infer.tar \
        && rm -f PP-LCNet_x1_0_doc_ori_infer.tar PP-LCNet_x1_0_textline_ori_infer.tar PP-OCRv5_server_det_infer.tar PP-OCRv5_server_rec_infer.tar \
        && mkdir -p "${HOME}/.paddlex/fonts" \
        && wget -P "${HOME}/.paddlex/fonts" https://paddle-model-ecology.bj.bcebos.com/paddlex/PaddleX3.0/fonts/PingFang-SC-Regular.ttf \
        && wget -P "${HOME}/.paddlex/fonts" https://paddle-model-ecology.bj.bcebos.com/paddlex/PaddleX3.0/fonts/simfang.ttf 

WORKDIR /app
COPY paddlex_hps_OCR_sdk/server .

ARG DEVICE_TYPE
ENV PADDLEX_HPS_DEVICE_TYPE=${DEVICE_TYPE}
CMD ["/bin/bash", "server.sh"]

# docker build . -t hps-paddleocr-ocrv5:latest
