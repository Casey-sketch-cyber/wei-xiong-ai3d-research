from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path
from urllib.parse import quote

import requests


REPO_ID = "WalkerCH/stream3d"
EXCLUDE_TERMS = (
    "avengers",
    "disney",
    "guardians_of_the_galaxy",
    "lego",
    "marvel",
    "nickelodeon",
    "nintendo",
    "pokemon",
    "spiderman",
    "star_wars",
    "teenage_mutant_ninja_turtles",
    "transformers",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--candidate-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default="https://hf-mirror.com")
    parser.add_argument("--add", type=int, default=70)
    parser.add_argument("--seed", type=int, default=20260714)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download(endpoint: str, repo_path: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{endpoint}/datasets/{REPO_ID}/resolve/main/{quote(repo_path, safe='/')}"
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, 7):
        headers = {}
        mode = "wb"
        if partial.exists() and partial.stat().st_size:
            headers["Range"] = f"bytes={partial.stat().st_size}-"
            mode = "ab"
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(45, 240)) as response:
                if response.status_code == 200 and mode == "ab":
                    mode = "wb"
                response.raise_for_status()
                with partial.open(mode) as handle:
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            partial.replace(target)
            return
        except Exception:
            if attempt == 6:
                raise
            time.sleep(attempt * 5)


def main() -> int:
    args = parse_args()
    records = json.loads(args.candidate_audit.read_text(encoding="utf-8"))
    existing = {str(row["object_name"]) for row in records}
    response = requests.get(f"{args.endpoint}/api/datasets/{REPO_ID}", timeout=240)
    response.raise_for_status()
    paths = [
        sibling["rfilename"]
        for sibling in response.json().get("siblings", [])
        if sibling.get("rfilename", "").startswith("GSO/")
        and sibling.get("rfilename", "").endswith("/model.glb")
    ]

    with zipfile.ZipFile(args.archive) as archive:
        archive_prefixes = {
            name.split("/models/")[0]
            for name in archive.namelist()
            if "/models/model_b_0_fragment_" in name
        }

    candidates = []
    for path in paths:
        object_name = path[len("GSO/") : -len("/model.glb")]
        if object_name in existing:
            continue
        if any(term in object_name.lower() for term in EXCLUDE_TERMS):
            continue
        if f"GSO/{object_name}_0" not in archive_prefixes:
            continue
        rank = hashlib.sha256(f"{args.seed}:{object_name}".encode()).hexdigest()
        candidates.append((rank, object_name, path))
    candidates.sort()

    added = 0
    for _, object_name, path in candidates[: args.add]:
        target = args.output / "candidates" / object_name / "model.glb"
        record = {
            "object_name": object_name,
            "source_repo": REPO_ID,
            "source_path": path,
            "local_path": str(target),
            "excluded_name": False,
        }
        try:
            if not target.exists():
                download(args.endpoint, path, target)
            record.update(
                {
                    "bytes": int(target.stat().st_size),
                    "sha256": file_sha256(target),
                    "status": "downloaded_for_solid_audit",
                }
            )
            added += 1
        except Exception as error:
            record.update({"status": "failed", "error": repr(error)})
        records.append(record)
        args.candidate_audit.write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("EXPAND", added, args.add, object_name, record["status"], flush=True)

    summary = {
        "repo": REPO_ID,
        "seed": args.seed,
        "eligible_candidates": len(candidates),
        "requested_additions": args.add,
        "successful_additions": added,
        "total_records": len(records),
    }
    (args.output / "candidate_expansion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if added == args.add else 2


if __name__ == "__main__":
    raise SystemExit(main())
