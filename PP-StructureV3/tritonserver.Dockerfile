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
        && wget --timeout=180 https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-DocLayout_plus-L_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-Chart2Table_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-DocBlockLayout_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_doc_ori_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/UVDoc_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_server_det_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_textline_ori_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_server_rec_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_table_cls_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/SLANeXt_wired_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/SLANet_plus_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/RT-DETR-L_wired_table_cell_det_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv4_server_seal_det_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-FormulaNet_plus-L_infer.tar \
            https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/RT-DETR-L_wireless_table_cell_det_infer.tar \
        && tar -xf PP-DocLayout_plus-L_infer.tar \
        && mv PP-DocLayout_plus-L_infer PP-DocLayout_plus-L \
        && rm -f PP-DocLayout_plus-L_infer.tar \
        && tar -xf PP-Chart2Table_infer.tar \
        && rm -f PP-Chart2Table_infer.tar \
        && tar -xf PP-DocBlockLayout_infer.tar \
        && mv PP-DocBlockLayout_infer PP-DocBlockLayout \
        && rm -f PP-DocBlockLayout_infer.tar \
        && tar -xf PP-LCNet_x1_0_doc_ori_infer.tar \
        && mv PP-LCNet_x1_0_doc_ori_infer PP-LCNet_x1_0_doc_ori \
        && rm -f PP-LCNet_x1_0_doc_ori_infer.tar \
        && tar -xf UVDoc_infer.tar \
        && mv UVDoc_infer UVDoc \
        && rm -f UVDoc_infer.tar \
        && tar -xf PP-OCRv5_server_det_infer.tar \
        && mv PP-OCRv5_server_det_infer PP-OCRv5_server_det \
        && rm -f PP-OCRv5_server_det_infer.tar \
        && tar -xf PP-LCNet_x1_0_textline_ori_infer.tar \
        && mv PP-LCNet_x1_0_textline_ori_infer PP-LCNet_x1_0_textline_ori \
        && rm -f PP-LCNet_x1_0_textline_ori_infer.tar \
        && tar -xf PP-OCRv5_server_rec_infer.tar \
        && mv PP-OCRv5_server_rec_infer PP-OCRv5_server_rec \
        && rm -f PP-OCRv5_server_rec_infer.tar \
        && tar -xf PP-LCNet_x1_0_table_cls_infer.tar \
        && mv PP-LCNet_x1_0_table_cls_infer PP-LCNet_x1_0_table_cls \
        && rm -f PP-LCNet_x1_0_table_cls_infer.tar \
        && tar -xf SLANeXt_wired_infer.tar \
        && mv SLANeXt_wired_infer SLANeXt_wired \
        && rm -f SLANeXt_wired_infer.tar \
        && tar -xf SLANet_plus_infer.tar \
        && mv SLANet_plus_infer SLANet_plus \
        && rm -f SLANet_plus_infer.tar \
        && tar -xf RT-DETR-L_wired_table_cell_det_infer.tar \
        && mv RT-DETR-L_wired_table_cell_det_infer RT-DETR-L_wired_table_cell_det \
        && rm -f RT-DETR-L_wired_table_cell_det_infer.tar \
        && tar -xf PP-OCRv4_server_seal_det_infer.tar \
        && mv PP-OCRv4_server_seal_det_infer PP-OCRv4_server_seal_det \
        && rm -f PP-OCRv4_server_seal_det_infer.tar \
        && tar -xf PP-FormulaNet_plus-L_infer.tar \
        && mv PP-FormulaNet_plus-L_infer PP-FormulaNet_plus-L \
        && rm -f PP-FormulaNet_plus-L_infer.tar \
        && tar -xf RT-DETR-L_wireless_table_cell_det_infer.tar \
        && mv RT-DETR-L_wireless_table_cell_det_infer RT-DETR-L_wireless_table_cell_det \
        && rm -f RT-DETR-L_wireless_table_cell_det_infer.tar \
        && mkdir -p "${HOME}/.paddlex/fonts" \
        && wget -P "${HOME}/.paddlex/fonts" https://paddle-model-ecology.bj.bcebos.com/paddlex/PaddleX3.0/fonts/PingFang-SC-Regular.ttf \
        && wget -P "${HOME}/.paddlex/fonts" https://paddle-model-ecology.bj.bcebos.com/paddlex/PaddleX3.0/fonts/simfang.ttf

WORKDIR /app
COPY paddlex_hps_PP-StructureV3_sdk/server .

ARG DEVICE_TYPE
ENV PADDLEX_HPS_DEVICE_TYPE=${DEVICE_TYPE}
CMD ["/bin/bash", "server.sh"]


# docker build . -t hps-paddleocr-structure-v3:latest
