#!/usr/bin/env python
"""Test script for PP-OCRv5 Gateway API."""

import argparse
import base64
import json
import sys
from pathlib import Path

import requests

DEFAULT_GATEWAY_URL = "http://localhost:8080"


def check_health(base_url: str) -> bool:
    """Check gateway health and readiness."""
    print("=== Health Check ===")
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        print(f"  /health: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"  /health: FAILED - {e}")
        return False

    try:
        resp = requests.get(f"{base_url}/health/ready", timeout=10)
        data = resp.json()
        print(f"  /health/ready: {resp.status_code} - {data}")
        if resp.status_code != 200:
            print("  Gateway is not ready. Is the Triton server running?")
            return False
    except Exception as e:
        print(f"  /health/ready: FAILED - {e}")
        return False

    print("  Gateway is healthy and ready.")
    return True


def ocr_with_file(base_url: str, file_path: str, **kwargs) -> dict:
    """Send a local file to the OCR API via base64 encoding."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    with open(path, "rb") as f:
        file_bytes = f.read()
    file_b64 = base64.b64encode(file_bytes).decode("utf-8")

    # Determine file type from extension
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        file_type = 0
    else:
        file_type = 1

    payload = {"file": file_b64, "fileType": file_type, **kwargs}
    return _send_ocr_request(base_url, payload)


def ocr_with_url(base_url: str, file_url: str, **kwargs) -> dict:
    """Send a URL to the OCR API."""
    payload = {"file": file_url, **kwargs}
    return _send_ocr_request(base_url, payload)


def _send_ocr_request(base_url: str, payload: dict) -> dict:
    """Send OCR request and return response."""
    print("\n=== OCR Request ===")
    print(f"  Payload keys: {list(payload.keys())}")
    if "file" in payload and len(payload["file"]) > 100:
        print(f"  file: <base64, {len(payload['file'])} chars>")
    else:
        print(f"  file: {payload.get('file', 'N/A')}")

    resp = requests.post(
        f"{base_url}/ocr",
        json=payload,
        timeout=120,
    )

    data = resp.json()
    print(f"\n=== OCR Response (status={resp.status_code}) ===")
    print(f"  logId: {data.get('logId')}")
    print(f"  errorCode: {data.get('errorCode')}")
    print(f"  errorMsg: {data.get('errorMsg')}")

    if data.get("errorCode", -1) != 0:
        print(f"\n  Error: {data.get('errorMsg')}")
        return data

    result = data.get("result", {})
    ocr_results = result.get("ocrResults", [])
    print(f"  Pages: {len(ocr_results)}")

    for i, page_result in enumerate(ocr_results):
        print(f"\n  --- Page {i} ---")
        pruned = page_result.get("prunedResult")
        if pruned:
            # prunedResult may be a JSON string or dict
            if isinstance(pruned, str):
                try:
                    pruned = json.loads(pruned)
                except json.JSONDecodeError:
                    pass

            if isinstance(pruned, dict):
                rec_texts = pruned.get("rec_texts", [])
                print(f"  Recognized texts ({len(rec_texts)}):")
                for j, text in enumerate(rec_texts):
                    print(f"    [{j}] {text}")
            else:
                print(f"  prunedResult: {pruned}")

        # Save visualization image if present
        ocr_image = page_result.get("ocrImage")
        if ocr_image:
            out_path = f"ocr_result_{i}.jpg"
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(ocr_image))
            print(f"  Visualization saved to: {out_path}")

    return data


def main():
    parser = argparse.ArgumentParser(description="Test PP-OCRv5 Gateway API")
    parser.add_argument(
        "--url",
        default=DEFAULT_GATEWAY_URL,
        help=f"Gateway URL (default: {DEFAULT_GATEWAY_URL})",
    )
    parser.add_argument(
        "--file",
        help="Local image or PDF file to OCR",
    )
    parser.add_argument(
        "--file-url",
        help="URL of image or PDF file to OCR",
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Only check health, skip OCR",
    )
    parser.add_argument(
        "--use-doc-orientation-classify",
        action="store_true",
        help="Enable document orientation classification",
    )
    parser.add_argument(
        "--use-textline-orientation",
        action="store_true",
        help="Enable text line orientation recognition",
    )
    parser.add_argument(
        "--no-visualize",
        action="store_true",
        help="Disable visualization output",
    )

    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    # Health check
    healthy = check_health(base_url)
    if args.health_only:
        sys.exit(0 if healthy else 1)

    if not healthy:
        print("\nGateway is not ready. Aborting OCR test.")
        sys.exit(1)

    if not args.file and not args.file_url:
        print("\nNo file specified. Use --file or --file-url to test OCR.")
        print("Example:")
        print(f"  python {sys.argv[0]} --file test_image.jpg")
        print(f"  python {sys.argv[0]} --file-url https://example.com/image.jpg")
        sys.exit(0)

    # Build extra kwargs
    kwargs = {}
    if args.use_doc_orientation_classify:
        kwargs["useDocOrientationClassify"] = True
    if args.use_textline_orientation:
        kwargs["useTextlineOrientation"] = True
    if args.no_visualize:
        kwargs["visualize"] = False

    if args.file:
        ocr_with_file(base_url, args.file, **kwargs)
    elif args.file_url:
        ocr_with_url(base_url, args.file_url, **kwargs)


if __name__ == "__main__":
    main()
