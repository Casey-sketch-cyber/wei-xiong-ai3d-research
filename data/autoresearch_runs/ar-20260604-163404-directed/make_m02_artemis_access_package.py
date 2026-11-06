#!/usr/bin/env python
"""Build an ArtEmis/WikiArt access request and authorization-record package."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXTERNAL = ROOT / "m02_external_steps_pack"
OUT = ROOT / "m02_artemis_access_package"
ZIP_PATH = OUT / "M02_ArtEmis_access_package.zip"


FILES = [
    (EXTERNAL / "artemis_access_request_template-zh.md", "artemis_access_request_template-zh.md"),
    (EXTERNAL / "artemis_access_live_check-zh.md", "artemis_access_live_check-zh.md"),
    (EXTERNAL / "artemis_authorization_record_template-zh.md", "artemis_authorization_record_template-zh.md"),
    (EXTERNAL / "post_artemis_data_plan-zh.md", "post_artemis_data_plan-zh.md"),
    (EXTERNAL / "human_evaluation_ethics_checklist-zh.md", "human_evaluation_ethics_checklist-zh.md"),
    (EXTERNAL / "external_steps_status.json", "external_steps_status.json"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_readme(file_count: int) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    text = f"""# M02 ArtEmis Access Package

日期：2026-06-05

用途：提交 ArtEmis/WikiArt 数据访问申请，并在授权后留档。

## 使用顺序

1. 打开 `artemis_access_request_template-zh.md`，复制其中英文研究说明到 ArtEmis 官方表单。
2. 阅读 `artemis_access_live_check-zh.md`，确认当前访问边界。
3. 获得授权后，填写 `artemis_authorization_record_template-zh.md`。
4. 按 `post_artemis_data_plan-zh.md` 放置受限数据，并运行：

```powershell
python check_external_steps.py
python run_m02_strict_followup.py
```

## 包内容

- ArtEmis 申请模板；
- 当前联网核验记录；
- 授权留档模板；
- 授权后正式 M02 接入计划；
- 人评/伦理检查清单；
- 当前 external steps 状态。

打包文件数：{file_count}

注意：本包不包含 ArtEmis 原始数据或 WikiArt 图像。
"""
    path = OUT / "README-zh.md"
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    readme = write_readme(len(FILES) + 1)
    rows = [(readme, "README-zh.md"), *FILES]
    manifest_rows = []
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for src, arcname in rows:
            archive.write(src, arcname)
            manifest_rows.append(
                {
                    "archive_path": arcname,
                    "source_path": str(src),
                    "bytes": src.stat().st_size,
                    "sha256": sha256(src),
                }
            )

    manifest_csv = OUT / "artemis_access_package_manifest.csv"
    with manifest_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["archive_path", "source_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "zip_path": str(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "files_in_zip": len(manifest_rows),
        "contains_restricted_data": False,
        "manifest_csv": str(manifest_csv),
    }
    (OUT / "artemis_access_package_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

