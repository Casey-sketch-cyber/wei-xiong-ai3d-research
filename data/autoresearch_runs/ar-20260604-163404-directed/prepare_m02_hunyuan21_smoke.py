#!/usr/bin/env python
"""Prepare a small M02 image set for Hunyuan3D 2.1 feasibility rerun."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HUMAN_PACK = ROOT / "m02_human_audit_pack"
OUT = ROOT / "m02_hunyuan21_rerun"
INPUTS = OUT / "inputs"

CURATED_IDS = [
    # Clearer single-object or central-subject cases.
    "Expressionism_request-86",
    "Neo-Impressionism_request-148",
    "Magic Realism_request-97",
    "Figurative Expressionism_request-2",
    # Harder scene / multi-object / abstract cases to test failure boundaries.
    "Shin-hanga_request-77",
    "Concretism_request-92",
    "Pop Art_request-54",
    "Gongbi_request-28",
]


def safe_name(request_id: str) -> str:
    return request_id.replace(" ", "_").replace("/", "_").replace("\\", "_")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    INPUTS.mkdir(parents=True, exist_ok=True)

    items_path = HUMAN_PACK / "annotation_items.csv"
    rows = list(csv.DictReader(items_path.open("r", encoding="utf-8-sig", newline="")))
    by_id = {row["request_id"]: row for row in rows}

    manifest_rows: list[dict[str, str]] = []
    missing: list[str] = []
    for idx, request_id in enumerate(CURATED_IDS, start=1):
        row = by_id.get(request_id)
        if not row:
            missing.append(request_id)
            continue
        src = HUMAN_PACK / row["original_image"]
        if not src.exists():
            missing.append(f"{request_id}: {src}")
            continue
        item_dir = INPUTS / safe_name(request_id)
        item_dir.mkdir(parents=True, exist_ok=True)
        dst = item_dir / "original.png"
        shutil.copy2(src, dst)
        manifest_rows.append(
            {
                "item_index": str(idx),
                "request_id": request_id,
                "safe_id": safe_name(request_id),
                "input_png": str(dst.relative_to(OUT)).replace("\\", "/"),
                "dominant_emotion": row["dominant_emotion"],
                "valence": row["valence"],
                "arousal": row["arousal"],
                "case_type": (
                    "clearer_subject"
                    if idx <= 4
                    else "hard_scene_or_abstract"
                ),
                "description": row["description"],
                "emotional_impact": row["emotional_impact"],
            }
        )

    if missing:
        raise SystemExit("Missing curated samples: " + "; ".join(missing))

    manifest_path = OUT / "hunyuan21_smoke_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    summary = {
        "experiment": "m02_hunyuan21_smoke",
        "model_target": "Hunyuan3D 2.1",
        "n_samples": len(manifest_rows),
        "inputs_dir": str(INPUTS),
        "manifest": str(manifest_path),
        "selection_policy": "4 clearer central-subject paintings plus 4 hard scene/abstract paintings",
        "stop_rule": "Stop after small-scale feasibility rerun and report whether M02 human rating is viable.",
    }
    (OUT / "hunyuan21_smoke_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    readme = [
        "# M02 Hunyuan3D 2.1 Small Rerun",
        "",
        "Purpose: test whether a stronger textured image-to-3D model can rescue M02 from the gray, untextured TripoSR failure mode.",
        "",
        f"Samples: {len(manifest_rows)} paintings.",
        "",
        "Selection:",
        "",
        "- 4 clearer central-subject images.",
        "- 4 hard scene/abstract images.",
        "",
        "Decision boundary:",
        "",
        "- If textured outputs preserve recognizable subject/material/style cues, M02 can continue toward human evaluation.",
        "- If outputs remain semantic blocks or unrelated assets, M02 should be reframed as an art-to-3D failure-mode/method-development problem.",
    ]
    (OUT / "README-zh.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
