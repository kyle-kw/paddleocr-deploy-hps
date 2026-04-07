#!/usr/bin/env python
"""Test script for PP-StructureV3 Gateway API."""

import argparse
import base64
import json
import sys
from pathlib import Path

import requests

DEFAULT_GATEWAY_URL = "http://localhost:8081"


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


def layout_parsing_with_file(base_url: str, file_path: str, **kwargs) -> dict:
    """Send a local file to the layout-parsing API via base64 encoding."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    with open(path, "rb") as f:
        file_bytes = f.read()
    file_b64 = base64.b64encode(file_bytes).decode("utf-8")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        file_type = 0
    else:
        file_type = 1

    payload = {"file": file_b64, "fileType": file_type, **kwargs}
    return _send_request(base_url, payload)


def layout_parsing_with_url(base_url: str, file_url: str, **kwargs) -> dict:
    """Send a URL to the layout-parsing API."""
    payload = {"file": file_url, **kwargs}
    return _send_request(base_url, payload)


def _send_request(base_url: str, payload: dict) -> dict:
    """Send layout-parsing request and return response."""
    print("\n=== Layout Parsing Request ===")
    print(f"  Payload keys: {list(payload.keys())}")
    if "file" in payload and len(payload["file"]) > 100:
        print(f"  file: <base64, {len(payload['file'])} chars>")
    else:
        print(f"  file: {payload.get('file', 'N/A')}")

    resp = requests.post(
        f"{base_url}/layout-parsing",
        json=payload,
        timeout=300,
    )

    data = resp.json()
    print(f"\n=== Response (status={resp.status_code}) ===")
    print(f"  logId: {data.get('logId')}")
    print(f"  errorCode: {data.get('errorCode')}")
    print(f"  errorMsg: {data.get('errorMsg')}")

    if data.get("errorCode", -1) != 0:
        print(f"\n  Error: {data.get('errorMsg')}")
        return data

    result = data.get("result", {})
    parsing_results = result.get("layoutParsingResults", [])
    print(f"  Pages: {len(parsing_results)}")

    for i, page_result in enumerate(parsing_results):
        print(f"\n  --- Page {i} ---")

        # Show pruned result summary
        pruned = page_result.get("prunedResult")
        if pruned:
            if isinstance(pruned, str):
                try:
                    pruned = json.loads(pruned)
                except json.JSONDecodeError:
                    pass
            if isinstance(pruned, dict):
                layout_elements = pruned.get("layoutElements", [])
                print(f"  Layout elements: {len(layout_elements)}")
                for j, elem in enumerate(layout_elements):
                    label = elem.get("label", "unknown")
                    text = elem.get("text", "")
                    preview = text[:80] + "..." if len(text) > 80 else text
                    print(f"    [{j}] {label}: {preview}")
            else:
                text = str(pruned)
                print(f"  prunedResult: {text[:200]}...")

        # Save markdown output
        markdown = page_result.get("markdown")
        if markdown:
            md_dir = Path(f"markdown_{i}")
            md_dir.mkdir(exist_ok=True)
            md_text = markdown.get("text", "")
            (md_dir / "doc.md").write_text(md_text)
            print(f"  Markdown saved to: {md_dir / 'doc.md'}")
            print(f"  Markdown preview: {md_text[:200]}...")

            # Save embedded images
            images = markdown.get("images", {})
            for img_name, img_data in images.items():
                img_path = md_dir / img_name
                img_path.parent.mkdir(parents=True, exist_ok=True)
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"  Image saved to: {img_path}")

        # Save output visualization images
        output_images = page_result.get("outputImages")
        if output_images:
            for img_name, img_data in output_images.items():
                out_path = f"{img_name}_{i}.jpg"
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"  Visualization saved to: {out_path}")

    return data


def main():
    parser = argparse.ArgumentParser(description="Test PP-StructureV3 Gateway API")
    parser.add_argument(
        "--url",
        default=DEFAULT_GATEWAY_URL,
        help=f"Gateway URL (default: {DEFAULT_GATEWAY_URL})",
    )
    parser.add_argument("--file", help="Local image or PDF file")
    parser.add_argument("--file-url", help="URL of image or PDF file")
    parser.add_argument(
        "--health-only", action="store_true", help="Only check health"
    )
    parser.add_argument(
        "--use-doc-orientation-classify", action="store_true",
        help="Enable document orientation classification",
    )
    parser.add_argument(
        "--use-textline-orientation", action="store_true",
        help="Enable text line orientation recognition",
    )
    parser.add_argument(
        "--use-seal-recognition", action="store_true",
        help="Enable seal recognition",
    )
    parser.add_argument(
        "--no-table-recognition", action="store_true",
        help="Disable table recognition",
    )
    parser.add_argument(
        "--no-formula-recognition", action="store_true",
        help="Disable formula recognition",
    )
    parser.add_argument(
        "--use-chart-recognition", action="store_true",
        help="Enable chart recognition",
    )
    parser.add_argument(
        "--no-visualize", action="store_true",
        help="Disable visualization output",
    )

    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    healthy = check_health(base_url)
    if args.health_only:
        sys.exit(0 if healthy else 1)

    if not healthy:
        print("\nGateway is not ready. Aborting test.")
        sys.exit(1)

    if not args.file and not args.file_url:
        print("\nNo file specified. Use --file or --file-url to test.")
        print("Example:")
        print(f"  python {sys.argv[0]} --file document.pdf")
        print(f"  python {sys.argv[0]} --file test_image.png")
        sys.exit(0)

    kwargs = {}
    if args.use_doc_orientation_classify:
        kwargs["useDocOrientationClassify"] = True
    if args.use_textline_orientation:
        kwargs["useTextlineOrientation"] = True
    if args.use_seal_recognition:
        kwargs["useSealRecognition"] = True
    if args.no_table_recognition:
        kwargs["useTableRecognition"] = False
    if args.no_formula_recognition:
        kwargs["useFormulaRecognition"] = False
    if args.use_chart_recognition:
        kwargs["useChartRecognition"] = True
    if args.no_visualize:
        kwargs["visualize"] = False

    if args.file:
        layout_parsing_with_file(base_url, args.file, **kwargs)
    elif args.file_url:
        layout_parsing_with_url(base_url, args.file_url, **kwargs)


if __name__ == "__main__":
    main()
