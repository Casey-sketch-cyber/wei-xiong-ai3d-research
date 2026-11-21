"""Audit a fixed visual sample and PowerPaint coverage from the frozen CMA run."""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from analyze_native_main import ARMS, MAX_ATTEMPTS, POWERPAINT_SAFETY, validate_source
from latent_mask_diagnostic import LUMA_WEIGHTS, read_pixels
from run_followup import NATIVE_MAIN_PROTOCOL, PAIRED_SEED
from run_latent_aligned import PROTOCOL
from run_pilot import SIZE, STRATA, read_json, sha256

AUDIT_SEED = 20261121
SAMPLE_SIZE = 12
ROWS_PER_SHEET = 3
PANELS = (("shared", "lama", "LaMa (shared mask)"), ("diffusion", "sdxl", "SDXL (shared mask)"))


def read_arm(root, key, source, source_hash):
    arm, models, aperture = ARMS[key]
    run_dir = root / arm
    plan_path = run_dir / "prepared.json"
    plan = read_json(plan_path)
    if (
        plan["protocol"] != PROTOCOL or plan["reference_protocol"] != NATIVE_MAIN_PROTOCOL
        or plan["arm"] != arm or plan["input_aperture"] != aperture
        or plan["reference_plan_sha256"] != source_hash or plan["cases"] != source["cases"]
        or plan["model_seeds"] != {model: [PAIRED_SEED] for model in models}
    ):
        raise ValueError(f"Arm does not match the frozen sample: {plan_path}")
    diagnostic_path = root / "diagnostics" / f"{arm}.json"
    diagnostic = read_json(diagnostic_path)
    if (
        diagnostic["protocol"] != "reconstruction-diagnostics-v1" or diagnostic["source_protocol"] != PROTOCOL
        or diagnostic["source_arm"] != arm or diagnostic["input_aperture"] != aperture
        or diagnostic["prepared_sha256"] != sha256(plan_path)
        or diagnostic["reference_plan_sha256"] != source_hash
    ):
        raise ValueError(f"Diagnostics do not match the frozen run: {diagnostic_path}")
    rows = {(row["case_id"], row["model"], row["seed"]): row for row in diagnostic["rows"]}
    if len(rows) != len(diagnostic["rows"]):
        raise ValueError(f"Duplicate diagnostic rows: {diagnostic_path}")
    return run_dir, rows, sha256(diagnostic_path)


def artwork_metadata(case):
    return {key: case[key] for key in ("artwork_id", "stratum", "title", "artist", "medium", "source_url", "rights")}


def read_sample(prepared_dir, arms, case):
    case_id = case["case_id"]
    original = read_pixels(prepared_dir / "originals" / f"{case_id}.png", case["crop_sha256"])
    mask = read_pixels(prepared_dir / "masks" / case["mask_file"], case["mask_sha256"]) > 0
    if (
        original.shape != (SIZE, SIZE, 3) or original.dtype != np.uint8 or mask.shape != (SIZE, SIZE)
        or not mask.any() or mask.sum() != case["mask_pixels"]
    ):
        raise ValueError(f"Invalid frozen crop or scoring mask: {case_id}")
    ys, xs = np.where(mask)
    sample = {
        "case_id": case_id, **artwork_metadata(case), "family": case["family"], "target_area": case["target_area"],
        "mask_pixels": case["mask_pixels"], "mask_bbox_xyxy_exclusive": [
            int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1,
        ],
        "original_sha256": case["crop_sha256"], "mask_sha256": case["mask_sha256"], "outputs": {},
    }
    images = [original]
    for arm_key, model, _ in PANELS:
        run_dir, rows, _ = arms[arm_key]
        row = rows[case_id, model, PAIRED_SEED]
        if (row["artwork_id"], row["stratum"]) != (case["artwork_id"], case["stratum"]):
            raise ValueError(f"Diagnostic row identity mismatch: {case_id}/{model}")
        output = run_dir / "restored" / f"{case_id}__{model}__s{PAIRED_SEED}.png"
        restored = read_pixels(output, row["restored_sha256"])
        if restored.shape != original.shape or restored.dtype != original.dtype:
            raise ValueError(f"Invalid restored crop: {output}")
        if not np.array_equal(restored[~mask], original[~mask]):
            raise ValueError(f"Original context changed: {output}")
        difference = restored[mask].astype(np.int16) - original[mask].astype(np.int16)
        mae = float(np.abs(difference).mean() / 255)
        if mae != row["masked_mae"] or not np.isfinite(row["local_lpips"]):
            raise ValueError(f"Invalid reconstruction metrics: {output}")
        sample["outputs"][model] = {
            "sha256": row["restored_sha256"], "outside_mask_identical": True, "masked_mae": mae,
            "local_lpips": row["local_lpips"], "signed_luma_error": float(difference.mean(0) @ LUMA_WEIGHTS / 255),
        }
        images.append(restored)
    return sample, images


def draw_sheet(samples, destination, first):
    page_margin, panel_gap, row_header = 16, 12, 30
    labels = ("Original frozen crop", *(title for _, _, title in PANELS))
    columns = [page_margin + index * (SIZE + panel_gap) for index in range(len(labels))]
    width = columns[-1] + SIZE + page_margin
    height = 2 * page_margin + row_header + len(samples) * (row_header + SIZE + panel_gap)
    sheet = Image.new("RGB", (width, height), (244, 244, 244))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    for x, title in zip(columns, labels, strict=True):
        draw.text((x, page_margin), title, fill="black", font=font)
    y = page_margin + row_header
    for rank, (sample, images) in enumerate(samples, first):
        heading = (
            f"{rank:02d}  {sample['stratum']}  |  {sample['family']}  {sample['target_area']:.0%}"
            f"  |  {sample['case_id']}  |  {sample['artwork_id']}"
        )
        draw.text((page_margin, y), heading, fill="black", font=font)
        for x, image in zip(columns, images, strict=True):
            sheet.paste(Image.fromarray(image), (x, y + row_header))
        y += row_header + SIZE + panel_gap
    sheet.save(destination)


def coverage(cases, blocked):
    return {
        "planned_cases": len(cases), "blocked_cases": sum(case["case_id"] in blocked for case in cases),
        "planned_works": len({case["artwork_id"] for case in cases}),
        "blocked_works": len({case["artwork_id"] for case in cases if case["case_id"] in blocked}),
    }


def powerpaint_missingness(run_dir, diagnostic_rows, cases, log):
    planned = {case["case_id"]: case for case in cases}
    attempt_pattern = re.compile(rf"^(.+)__powerpaint__s{PAIRED_SEED}: attempt ([12]): (.+)$")
    attempts = defaultdict(list)
    for line in log.read_text(encoding="utf-8").splitlines():
        if match := attempt_pattern.fullmatch(line):
            case_id, number, error = match.groups()
            attempts[case_id].append((int(number), error))

    completed = {case_id for case_id, model, seed in diagnostic_rows if (model, seed) == ("powerpaint", PAIRED_SEED)}
    blocked = {}
    blocked_by_artwork = defaultdict(list)
    filename = re.compile(rf"^(.+)__powerpaint__s{PAIRED_SEED}$")
    for path in sorted((run_dir / "failures").glob("*__powerpaint__*.json")):
        match = filename.fullmatch(path.stem)
        if not match or match[1] not in planned:
            raise ValueError(f"Unexpected PowerPaint failure record: {path}")
        case_id = match[1]
        failure = read_json(path)
        expected_attempt_log = [(number, POWERPAINT_SAFETY) for number in range(1, MAX_ATTEMPTS + 1)]
        if (
            type(failure["attempts"]) is not int or failure["attempts"] != MAX_ATTEMPTS
            or failure["error"] != POWERPAINT_SAFETY or attempts[case_id] != expected_attempt_log
        ):
            raise ValueError(f"Could not confirm both safety-check attempts: {case_id}")
        case = planned[case_id]
        blocked[case_id] = {"case_id": case_id, "family": case["family"], "target_area": case["target_area"],
                            "verified_attempts": [number for number, _ in attempts[case_id]]}
        blocked_by_artwork[case["artwork_id"]].append(blocked[case_id])
    run = read_json(run_dir / "run_powerpaint.json")
    if (
        set(attempts) != blocked.keys() or completed & blocked.keys() or completed | blocked.keys() != planned.keys()
        or (run["model"], run["completed"], run["failed"]) != ("powerpaint", len(completed), len(blocked))
    ):
        raise ValueError("PowerPaint scored, blocked and attempted counts disagree with the frozen plan")

    works = {case["artwork_id"]: case for case in cases}
    groups = sorted({case["medium"] for case in cases})
    conditions = sorted({(case["family"], case["target_area"]) for case in cases})
    return {
        **coverage(cases, blocked), "scored_cases": len(completed),
        "verified_safety_block_attempts": sum(len(rows) for rows in attempts.values()), "log_sha256": sha256(log),
        "by_stratum": {group: coverage([case for case in cases if case["stratum"] == group], blocked)
                       for group in STRATA},
        "by_catalog_medium": [
            {"medium": medium, **coverage([case for case in cases if case["medium"] == medium], blocked)}
            for medium in groups
        ],
        "by_condition": [
            {"family": family, "target_area": area, **coverage([
                case for case in cases if (case["family"], case["target_area"]) == (family, area)
            ], blocked)} for family, area in conditions
        ],
        "blocked_artworks": [
            {**artwork_metadata(works[artwork]), "planned_cases": sum(case["artwork_id"] == artwork for case in cases),
             "blocked_cases": len(rows), "blocked_case_records": rows}
            for artwork, rows in sorted(blocked_by_artwork.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Frozen CMA native-main run root")
    parser.add_argument("--sheet-dir", type=Path, required=True, help="New directory for native-size contact sheets")
    parser.add_argument("--output", type=Path, required=True, help="New JSON audit file")
    parser.add_argument("--powerpaint-log", type=Path, help="Override the original PowerPaint model log path")
    args = parser.parse_args()
    root, sheet_dir, output = (value.resolve() for value in (args.root, args.sheet_dir, args.output))
    if output.suffix != ".json" or any(path.exists() or path.is_relative_to(root) for path in (sheet_dir, output)):
        parser.error("Sheet directory and JSON output must be new paths outside the frozen run")
    if output == sheet_dir:
        parser.error("Sheet directory and JSON output must differ")
    log = args.powerpaint_log or root.parent.parent / "logs" / root.name / "native-main-powerpaint.log"

    plan_path = root / "prepared" / "prepared.json"
    source = read_json(plan_path)
    validate_source(source)
    source_hash = sha256(plan_path)
    arms = {key: read_arm(root, key, source, source_hash) for key, _, _ in PANELS}
    case_by_id = {case["case_id"]: case for case in source["cases"]}
    population = sorted(case_by_id)
    rng = np.random.Generator(np.random.PCG64(AUDIT_SEED))
    selected = rng.choice(population, size=SAMPLE_SIZE, replace=False).tolist()
    samples = [read_sample(plan_path.parent, arms, case_by_id[case_id]) for case_id in selected]
    run, diagnostics, _ = arms["diffusion"]
    missingness = powerpaint_missingness(run, diagnostics, source["cases"], log)

    sheet_dir.mkdir(parents=True)
    sheets = []
    for start in range(0, len(samples), ROWS_PER_SHEET):
        page = sheet_dir / f"native-audit-{start // ROWS_PER_SHEET + 1:02d}.png"
        group = samples[start:start + ROWS_PER_SHEET]
        draw_sheet(group, page, start + 1)
        sheets.append({"filename": page.name, "case_ids": [sample["case_id"] for sample, _ in group],
                       "sha256": sha256(page)})
    report = {
        "protocol": "native-main-saved-output-audit-v1", "source_plan_sha256": source_hash,
        "diagnostic_sha256": {key: value[2] for key, value in arms.items()},
        "sampling": {"rng": "NumPy PCG64", "seed": AUDIT_SEED, "population_case_count": len(population),
                     "sampling_frame": "sorted frozen case IDs, uniform without replacement",
                     "selected_case_ids_in_draw_order": selected},
        "inference_seed": PAIRED_SEED, "contact_sheets": sheets,
        "visual_sample": [sample for sample, _ in samples], "powerpaint": missingness,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Verified {len(samples)} cases and saved {len(sheets)} sheets. PowerPaint blocked "
          f"{missingness['blocked_cases']}/{missingness['planned_cases']} cases.", flush=True)


if __name__ == "__main__":
    main()
