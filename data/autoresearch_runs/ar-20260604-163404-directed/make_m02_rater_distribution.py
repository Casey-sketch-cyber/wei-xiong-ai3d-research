#!/usr/bin/env python
"""Build a self-contained M02 rater distribution zip."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HUMAN = ROOT / "m02_human_audit_pack"
EXTERNAL = ROOT / "m02_external_steps_pack"
OUT = ROOT / "m02_rater_distribution"
ZIP_PATH = OUT / "M02_rater_package.zip"


STATIC_FILES = [
    (HUMAN / "rating_tool.html", "rating_tool.html"),
    (HUMAN / "RATER_QUICKSTART-zh.md", "RATER_QUICKSTART-zh.md"),
    (HUMAN / "README-zh.md", "human_audit_README-zh.md"),
    (HUMAN / "annotation_template.csv", "annotation_template.csv"),
    (HUMAN / "annotation_items.csv", "annotation_items.csv"),
    (EXTERNAL / "rater_consent_template-zh.md", "rater_consent_template-zh.md"),
    (EXTERNAL / "rater_metadata_template.csv", "rater_metadata_template.csv"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files() -> list[tuple[Path, str]]:
    rows = list(STATIC_FILES)
    for path in sorted((HUMAN / "images").rglob("*.png")):
        rows.append((path, path.relative_to(HUMAN).as_posix()))
    return rows


def write_distribution_readme(file_count: int) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    text = f"""# M02 Rater Distribution

日期：2026-06-04

用途：给真人评价者的自包含评分包。

## 使用方法

1. 解压 `M02_rater_package.zip`。
2. 阅读 `RATER_QUICKSTART-zh.md` 和 `rater_consent_template-zh.md`。
3. 用浏览器打开 `rating_tool.html`。
4. 完成 50 个样本评分后点击 `Export CSV`。
5. 将导出的 CSV 命名为 `annotation_rater01.csv`、`annotation_rater02.csv` 等。
6. 把 CSV 交回，并放入主实验目录的 `m02_human_audit_pack\\rater_exports\\`。

## 包内容

- 评分工具：`rating_tool.html`
- 快速说明：`RATER_QUICKSTART-zh.md`
- 评分模板：`annotation_template.csv`
- 样本元数据：`annotation_items.csv`
- 评价者同意模板：`rater_consent_template-zh.md`
- 评价者背景信息表：`rater_metadata_template.csv`
- 图片：50 个样本的 original/render PNG，共 100 张

打包文件数：{file_count}
"""
    path = OUT / "README-zh.md"
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = collect_files()
    readme = write_distribution_readme(len(files) + 1)
    files_with_readme = [(readme, "README-zh.md"), *files]

    manifest_rows = []
    with ZIP_PATH.open("wb") as raw:
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for src, arcname in files_with_readme:
                archive.write(src, arcname)
                manifest_rows.append(
                    {
                        "archive_path": arcname,
                        "source_path": str(src),
                        "bytes": src.stat().st_size,
                        "sha256": sha256(src),
                    }
                )

    manifest_csv = OUT / "rater_package_manifest.csv"
    with manifest_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["archive_path", "source_path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "zip_path": str(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "files_in_zip": len(manifest_rows),
        "image_pngs": sum(1 for row in manifest_rows if str(row["archive_path"]).startswith("images/") and str(row["archive_path"]).endswith(".png")),
        "manifest_csv": str(manifest_csv),
    }
    (OUT / "rater_package_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
