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

WORKDIR /app
COPY paddlex_hps_PaddleOCR-VL-1.5_sdk/server .

ENV HOME=/root
RUN mkdir -p "${HOME}/.paddlex/official_models" \
        && cd "${HOME}/.paddlex/official_models" \
        && wget https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/UVDoc_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_doc_ori_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-DocLayoutV3_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PaddleOCR-VL-1.5_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv4_server_seal_det_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv4_server_rec_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-Chart2Table_infer.tar \
        && tar -xf UVDoc_infer.tar \
        && mv UVDoc_infer UVDoc \
        && tar -xf PP-LCNet_x1_0_doc_ori_infer.tar \
        && mv PP-LCNet_x1_0_doc_ori_infer PP-LCNet_x1_0_doc_ori \
        && tar -xf PP-DocLayoutV3_infer.tar \
        && mv PP-DocLayoutV3_infer PP-DocLayoutV3 \
        && tar -xf PaddleOCR-VL-1.5_infer.tar \
        && mv PaddleOCR-VL-1.5_infer PaddleOCR-VL-1.5 \
        && tar -xf PP-OCRv4_server_seal_det_infer.tar \
        && mv PP-OCRv4_server_seal_det_infer PP-OCRv4_server_seal_det \
        && tar -xf PP-OCRv4_server_rec_infer.tar \
        && mv PP-OCRv4_server_rec_infer PP-OCRv4_server_rec \
        && tar -xf PP-Chart2Table_infer.tar \
        && rm -f UVDoc_infer.tar PP-LCNet_x1_0_doc_ori_infer.tar PP-DocLayoutV3_infer.tar PaddleOCR-VL-1.5_infer.tar PP-OCRv4_server_seal_det_infer.tar PP-OCRv4_server_rec_infer.tar PP-Chart2Table_infer.tar  \
        && mkdir -p "${HOME}/.paddlex/fonts" \
        && wget -P "${HOME}/.paddlex/fonts" https://paddle-model-ecology.bj.bcebos.com/paddlex/PaddleX3.0/fonts/PingFang-SC-Regular.ttf \
        && wget -P "${HOME}/.paddlex/fonts" https://paddle-model-ecology.bj.bcebos.com/paddlex/PaddleX3.0/fonts/simfang.ttf

ARG DEVICE_TYPE
ENV PADDLEX_HPS_DEVICE_TYPE=${DEVICE_TYPE}
CMD ["/bin/bash", "server.sh"]
