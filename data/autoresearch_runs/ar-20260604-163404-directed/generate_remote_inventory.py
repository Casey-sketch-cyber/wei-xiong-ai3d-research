#!/usr/bin/env python
"""Generate an inventory report for key remote M03/M02 artifacts.

Requires SSH credentials through environment variables:

- REMOTE_HOST
- REMOTE_PORT
- REMOTE_USER
- REMOTE_PW
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "remote_artifact_inventory"

REMOTE_PATHS = [
    "/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_main100_curated_600",
    "/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_main100_res128_30x6",
    "/root/autodl-tmp/m03/outputs/m02_proxy/main100_triposr_renders",
    "/root/autodl-tmp/m03/outputs/m02_emoart50/triposr_runs",
    "/root/autodl-tmp/m03/outputs/m02_emoart50/eval",
    "/root/autodl-tmp/m03/outputs/m02_emoart100/triposr_runs",
    "/root/autodl-tmp/m03/outputs/m02_emoart100/eval",
    "/root/autodl-tmp/m03/datasets/objaverse_main100",
    "/root/autodl-tmp/m03/datasets/objaverse_main100_gt_curated",
    "/root/autodl-tmp/m03/datasets/emoart5k_m02_sample50",
    "/root/autodl-tmp/m03/datasets/emoart5k_m02_sample100",
]


REMOTE_SCRIPT = r"""
/root/miniconda3/bin/python - <<'PY'
import json, os, pathlib, time
paths = __PATHS__
out=[]
for p in paths:
    path=pathlib.Path(p)
    item={'path':p,'exists':path.exists(),'files':0,'dirs':0,'bytes':0,'sample_files':[]}
    if path.exists():
        for root, dirs, files in os.walk(path):
            item['dirs'] += len(dirs)
            for name in files:
                fp=pathlib.Path(root)/name
                item['files'] += 1
                try:
                    item['bytes'] += fp.stat().st_size
                except OSError:
                    pass
                if len(item['sample_files']) < 8:
                    item['sample_files'].append(str(fp))
    out.append(item)
print(json.dumps({'generated_at_remote_epoch': time.time(), 'items': out}, ensure_ascii=False, indent=2))
PY
"""


def run_remote_inventory() -> dict:
    host = os.environ.get("REMOTE_HOST", "connect.bjb2.seetacloud.com")
    port = int(os.environ.get("REMOTE_PORT", "13288"))
    user = os.environ.get("REMOTE_USER", "root")
    password = os.environ["REMOTE_PW"]
    cmd = REMOTE_SCRIPT.replace("__PATHS__", json.dumps(REMOTE_PATHS))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        _, stdout, stderr = client.exec_command(cmd, timeout=240)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace").strip()
        if err:
            raise RuntimeError(err)
        return json.loads(out)
    finally:
        client.close()


def write_markdown(data: dict) -> str:
    lines = [
        "# Remote Artifact Inventory",
        "",
        "Remote root: `/root/autodl-tmp/m03`",
        "",
        "| path | exists | files | dirs | bytes |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in data["items"]:
        lines.append(
            f"| `{item['path']}` | {item['exists']} | {item['files']} | {item['dirs']} | {item['bytes']} |"
        )
    lines.extend(["", "## Sample Files", ""])
    for item in data["items"]:
        lines.append(f"### `{item['path']}`")
        for sample in item.get("sample_files", []):
            lines.append(f"- `{sample}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data = run_remote_inventory()
    (OUT / "remote_artifact_inventory.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "remote_artifact_inventory.md").write_text(write_markdown(data), encoding="utf-8")
    print(json.dumps(
        {
            "status": "ok",
            "items": len(data["items"]),
            "existing_items": sum(1 for item in data["items"] if item["exists"]),
            "total_files": sum(int(item["files"]) for item in data["items"]),
            "total_bytes": sum(int(item["bytes"]) for item in data["items"]),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
