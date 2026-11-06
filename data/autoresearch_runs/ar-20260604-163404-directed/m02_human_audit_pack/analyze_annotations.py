#!/usr/bin/env python
"""Summarize M02 human annotation CSV files.

Run from this directory after evaluators fill copied annotation templates.
The script accepts one or more CSV files and writes aggregate outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


SCORE_FIELDS = [
    "emotion_preservation_1_5",
    "visual_evidence_preservation_1_5",
    "style_preservation_1_5",
    "geometry_usability_1_5",
    "multiview_stability_1_5",
    "overall_acceptability_1_5",
]

TEXT_FIELDS = [
    "most_influential_visual_factor",
    "lost_after_3d",
    "new_unwanted_cue",
    "notes",
]


def parse_score(raw: str, field: str, row_id: str) -> float | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        score = float(value)
    except ValueError as exc:
        raise ValueError(f"{row_id}: {field} must be numeric, got {value!r}") from exc
    if not (1 <= score <= 5):
        raise ValueError(f"{row_id}: {field} must be in [1, 5], got {score}")
    return score


def load_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [field for field in ["item_index", "request_id", *SCORE_FIELDS] if field not in reader.fieldnames]
            if missing:
                raise ValueError(f"{path}: missing required columns: {', '.join(missing)}")
            for row_number, row in enumerate(reader, start=2):
                row = dict(row)
                row["_source_file"] = path.name
                row["_row_number"] = str(row_number)
                rows.append(row)
    return rows


def valid_annotation_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    valid: list[dict[str, object]] = []
    for row in rows:
        row_id = f"{row['_source_file']}:{row['_row_number']} request_id={row.get('request_id', '')}"
        scores = {field: parse_score(str(row.get(field, "")), field, row_id) for field in SCORE_FIELDS}
        if all(value is None for value in scores.values()):
            continue
        if any(value is None for value in scores.values()):
            missing = [field for field, value in scores.items() if value is None]
            raise ValueError(f"{row_id}: partial scoring is not allowed; missing {', '.join(missing)}")
        valid.append(
            {
                **row,
                **scores,
                "mean_score": mean(scores.values()),
            }
        )
    return valid


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None

    def ranks(values: list[float]) -> list[float]:
        order = sorted(enumerate(values), key=lambda item: item[1])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and order[j + 1][1] == order[i][1]:
                j += 1
            avg_rank = (i + j + 2) / 2
            for k in range(i, j + 1):
                out[order[k][0]] = avg_rank
            i = j + 1
        return out

    rx = ranks(xs)
    ry = ranks(ys)
    mx = mean(rx)
    my = mean(ry)
    numerator = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    dx = math.sqrt(sum((x - mx) ** 2 for x in rx))
    dy = math.sqrt(sum((y - my) ** 2 for y in ry))
    if dx == 0 or dy == 0:
        return None
    return numerator / (dx * dy)


def summarize(valid_rows: list[dict[str, object]], items_path: Path | None) -> tuple[dict[str, object], list[dict[str, object]]]:
    by_item: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in valid_rows:
        by_item[str(row["request_id"])].append(row)

    item_meta: dict[str, dict[str, str]] = {}
    if items_path and items_path.exists():
        with items_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                item_meta[row["request_id"]] = row

    item_rows: list[dict[str, object]] = []
    for request_id, rows in sorted(by_item.items(), key=lambda item: min(int(str(r["item_index"])) for r in item[1])):
        out: dict[str, object] = {
            "request_id": request_id,
            "item_index": rows[0]["item_index"],
            "n_annotators": len({str(r.get("annotator_id", "")) or str(r["_source_file"]) for r in rows}),
        }
        meta = item_meta.get(request_id, {})
        for key in ["dominant_emotion", "valence", "arousal", "orig_top_emotion", "render_top_emotion", "js_render_to_orig"]:
            out[key] = meta.get(key, rows[0].get(key, ""))
        for field in SCORE_FIELDS:
            values = [float(r[field]) for r in rows]
            out[f"{field}_mean"] = mean(values)
            out[f"{field}_sd"] = pstdev(values) if len(values) > 1 else 0.0
        out["mean_score"] = mean(float(r["mean_score"]) for r in rows)
        item_rows.append(out)

    overall: dict[str, object] = {
        "n_scored_rows": len(valid_rows),
        "n_items_scored": len(item_rows),
        "n_unique_annotators": len({str(r.get("annotator_id", "")) or str(r["_source_file"]) for r in valid_rows}),
    }
    for field in SCORE_FIELDS:
        values = [float(row[field]) for row in valid_rows]
        overall[field] = {
            "mean": mean(values) if values else None,
            "sd": pstdev(values) if len(values) > 1 else 0.0,
            "n": len(values),
        }

    if item_rows:
        proxy_rows = [row for row in item_rows if str(row.get("js_render_to_orig", "")).strip()]
        for field in SCORE_FIELDS:
            xs: list[float] = []
            ys: list[float] = []
            for row in proxy_rows:
                try:
                    xs.append(float(row["js_render_to_orig"]))
                    ys.append(float(row[f"{field}_mean"]))
                except (TypeError, ValueError):
                    continue
            overall[f"spearman_js_vs_{field}"] = spearman(xs, ys)

    text_counts = {field: sum(1 for row in valid_rows if str(row.get(field, "")).strip()) for field in TEXT_FIELDS}
    overall["free_text_counts"] = text_counts
    return overall, item_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize M02 human annotation CSV files.")
    parser.add_argument("csv", nargs="+", type=Path, help="Filled annotation CSV file(s).")
    parser.add_argument("--items", type=Path, default=Path("annotation_items.csv"), help="annotation_items.csv path.")
    parser.add_argument("--out-dir", type=Path, default=Path("analysis_outputs"), help="Output directory.")
    args = parser.parse_args()

    rows = load_rows(args.csv)
    valid_rows = valid_annotation_rows(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not valid_rows:
        summary = {
            "status": "no_completed_scores",
            "message": "No complete annotation rows were found. Fill all 1-5 score columns before analysis.",
            "n_input_rows": len(rows),
            "n_scored_rows": 0,
        }
        (args.out_dir / "human_annotation_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    overall, item_rows = summarize(valid_rows, args.items)
    write_csv(args.out_dir / "human_annotation_item_summary.csv", item_rows)
    (args.out_dir / "human_annotation_summary.json").write_text(
        json.dumps(overall, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(overall, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

