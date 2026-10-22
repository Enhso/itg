"""Submit and download a short Foundry video-generation job.

This is optional: the deterministic renderer is the authoritative demo path.
Set FOUNDRY_OPENAI_ENDPOINT to the Azure OpenAI-compatible resource endpoint and
FOUNDRY_VIDEO_MODEL to an available video deployment before running.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen


def token() -> str:
    return subprocess.check_output(
        ["az", "account", "get-access-token", "--resource", "https://cognitiveservices.azure.com", "--query", "accessToken", "-o", "tsv"],
        text=True,
    ).strip()


def request(method: str, url: str, bearer: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(url, data=body, method=method, headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"})
    with urlopen(req) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/examples/foundry-generated.mp4"))
    args = parser.parse_args()
    endpoint = os.environ["FOUNDRY_OPENAI_ENDPOINT"].rstrip("/")
    model = os.environ["FOUNDRY_VIDEO_MODEL"]
    api_version = os.getenv("FOUNDRY_VIDEO_API_VERSION", "preview")
    bearer = token()
    base = f"{endpoint}/openai/v1/video/generations"
    job = request(
        "POST",
        f"{base}/jobs?api-version={api_version}",
        bearer,
        {
            "model": model,
            "prompt": "A short synthetic football broadcast clip: fictional Corvane FC versus fictional Tessaly Athletic, generic uniforms, no logos, no readable text, a visible away-team high press in a stylized stadium.",
            "width": 854,
            "height": 480,
            "n_seconds": 5,
            "n_variants": 1,
        },
    )
    job_id = job["id"]
    while True:
        status = request("GET", f"{base}/jobs/{job_id}?api-version={api_version}", bearer)
        if status.get("status") in {"succeeded", "failed", "cancelled"}:
            break
        time.sleep(5)
    if status.get("status") != "succeeded":
        raise RuntimeError(json.dumps(status))
    generation_id = status["generations"][0]["id"]
    req = Request(f"{base}/{generation_id}/content/video?api-version={api_version}", headers={"Authorization": f"Bearer {bearer}"})
    with urlopen(req) as response:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(response.read())
    print(args.output)


if __name__ == "__main__":
    main()
