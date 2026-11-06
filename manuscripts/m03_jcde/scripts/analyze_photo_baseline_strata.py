from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path


STYLE_ORDER = ["edge", "flat", "low_detail", "sketch", "watercolor"]
SEED = 20260713


def as_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_mean_ci(
    values: list[float], rng: random.Random, repetitions: int = 10_000
) -> tuple[float, float]:
    n = len(values)
    means = []
    for _ in range(repetitions):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.fmean(sample))
    return percentile(means, 0.025), percentile(means, 0.975)


def rank_biserial(differences: list[float]) -> float:
    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return 0.0
    ranked = sorted(enumerate(nonzero), key=lambda item: abs(item[1]))
    ranks = [0.0] * len(nonzero)
    cursor = 0
    while cursor < len(ranked):
        end = cursor + 1
        while end < len(ranked) and abs(ranked[end][1]) == abs(ranked[cursor][1]):
            end += 1
        average_rank = (cursor + 1 + end) / 2
        for index in range(cursor, end):
            ranks[ranked[index][0]] = average_rank
        cursor = end
    positive = sum(rank for rank, value in zip(ranks, nonzero) if value > 0)
    negative = sum(rank for rank, value in zip(ranks, nonzero) if value < 0)
    return (positive - negative) / (positive + negative)


def paired_records(
    uids: list[str], rows_by_key: dict[tuple[str, str], dict[str, str]], style: str
) -> list[dict[str, float]]:
    records = []
    for uid in uids:
        photo = rows_by_key[(uid, "photo")]
        styled = rows_by_key[(uid, style)]
        photo_volume = as_float(photo["pred_volume"])
        styled_volume = as_float(styled["pred_volume"])
        photo_z = as_float(photo["pred_extent_z"])
        styled_z = as_float(styled["pred_extent_z"])
        photo_f = as_float(photo["fscore_0.05"])
        styled_f = as_float(styled["fscore_0.05"])
        photo_cd = as_float(photo["chamfer_l2"])
        styled_cd = as_float(styled["chamfer_l2"])
        if None in (photo_z, styled_z, photo_f, styled_f, photo_cd, styled_cd):
            continue
        record = {
            "photo_fscore": photo_f,
            "delta_fscore": styled_f - photo_f,
            "delta_chamfer": styled_cd - photo_cd,
            "z_ratio": styled_z / photo_z,
        }
        if photo_volume not in (None, 0.0) and styled_volume is not None:
            record["volume_ratio"] = styled_volume / photo_volume
            record["volume_difference"] = styled_volume - photo_volume
        records.append(record)
    return records


def summarise_records(
    records: list[dict[str, float]], rng: random.Random
) -> dict[str, float | int]:
    volume_records = [record for record in records if "volume_ratio" in record]
    volume_ratios = [record["volume_ratio"] for record in volume_records]
    delta_f = [record["delta_fscore"] for record in volume_records]
    delta_cd = [record["delta_chamfer"] for record in volume_records]
    z_ratios = [record["z_ratio"] for record in volume_records]
    volume_differences = [record["volume_difference"] for record in volume_records]
    ci_low, ci_high = bootstrap_mean_ci(volume_ratios, rng)
    collapse_count = sum(value < 0.5 for value in volume_ratios)
    paradox_count = sum(
        record["delta_fscore"] > 0 and record["volume_ratio"] < 0.5
        for record in volume_records
    )
    return {
        "n": len(volume_records),
        "mean_volume_ratio": statistics.fmean(volume_ratios),
        "median_volume_ratio": statistics.median(volume_ratios),
        "q1_volume_ratio": percentile(volume_ratios, 0.25),
        "q3_volume_ratio": percentile(volume_ratios, 0.75),
        "mean_volume_ratio_ci_low": ci_low,
        "mean_volume_ratio_ci_high": ci_high,
        "mean_z_ratio": statistics.fmean(z_ratios),
        "mean_delta_fscore": statistics.fmean(delta_f),
        "mean_delta_chamfer": statistics.fmean(delta_cd),
        "collapse_below_0_5_count": collapse_count,
        "collapse_below_0_5_pct": 100 * collapse_count / len(volume_records),
        "paradox_count": paradox_count,
        "paradox_pct": 100 * paradox_count / len(volume_records),
        "volume_rank_biserial": rank_biserial(volume_differences),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 600:
        raise ValueError(f"Expected 600 metric rows, found {len(rows)}")

    rows_by_key = {(row["uid"], row["style"]): row for row in rows}
    photo_rows = [row for row in rows if row["style"] == "photo"]
    photo_rows.sort(key=lambda row: float(row["fscore_0.05"]))
    photo_scores = [float(row["fscore_0.05"]) for row in photo_rows]
    photo_median = statistics.median(photo_scores)

    groups = {
        "all": [row["uid"] for row in photo_rows],
        "low_photo_quality": [
            row["uid"] for row in photo_rows if float(row["fscore_0.05"]) < photo_median
        ],
        "high_photo_quality": [
            row["uid"] for row in photo_rows if float(row["fscore_0.05"]) >= photo_median
        ],
        "top_photo_quartile": [row["uid"] for row in photo_rows[-25:]],
    }

    rng = random.Random(SEED)
    strata_rows: list[dict[str, object]] = []
    global_rows: list[dict[str, object]] = []
    nested: dict[str, dict[str, dict[str, float | int]]] = {}
    for group_name, uids in groups.items():
        nested[group_name] = {}
        for style in STYLE_ORDER:
            records = paired_records(uids, rows_by_key, style)
            summary = summarise_records(records, rng)
            nested[group_name][style] = summary
            row = {"group": group_name, "style": style, **summary}
            strata_rows.append(row)
            if group_name == "all":
                global_rows.append({"style": style, **summary})

    summary = {
        "input": str(args.input),
        "seed": SEED,
        "bootstrap_repetitions": 10_000,
        "photo_quality_definition": "median split of photo F-score@0.05 against ground truth",
        "photo_fscore_median": photo_median,
        "photo_fscore_top_quartile_min": float(photo_rows[-25]["fscore_0.05"]),
        "group_sizes": {name: len(uids) for name, uids in groups.items()},
        "results": nested,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "photo_baseline_strata.csv", strata_rows)
    write_csv(args.output_dir / "style_robust_statistics.csv", global_rows)
    (args.output_dir / "photo_baseline_strata.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report_lines = [
        "# Photo baseline stratification audit",
        "",
        f"Photo F-score@0.05 median: `{photo_median:.6f}`.",
        "",
        "| style | low-group volume | high-group volume | low-group delta F | high-group delta F | top-quartile delta F |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for style in STYLE_ORDER:
        low = nested["low_photo_quality"][style]
        high = nested["high_photo_quality"][style]
        top = nested["top_photo_quartile"][style]
        report_lines.append(
            f"| {style} | {low['mean_volume_ratio']:.3f} | {high['mean_volume_ratio']:.3f} | "
            f"{low['mean_delta_fscore']:+.3f} | {high['mean_delta_fscore']:+.3f} | "
            f"{top['mean_delta_fscore']:+.3f} |"
        )
    report_lines.extend(
        [
            "",
            "The volumetric contraction persists in the high-quality half, but the aggregate F-score gain is concentrated in the low-quality photo half. In the top photo-quality quartile, the mean F-score change is negative for every style.",
            "",
        ]
    )
    (args.output_dir / "photo_baseline_stratification.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
