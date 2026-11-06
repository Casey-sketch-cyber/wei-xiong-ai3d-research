from __future__ import annotations

import ast
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
M03 = ROOT / "experiments/m03_q2_confirmatory_20260715/results_final/artifacts_20260729"
M05 = ROOT / "data/autoresearch_runs/ar-20260903-m05-visrepair3d/04_full_experiment/outputs_formal_v2"
FORBIDDEN = {
    ".glb", ".gltf", ".obj", ".ply", ".stl", ".fbx", ".blend", ".pt", ".pth",
    ".ckpt", ".safetensors", ".onnx", ".npz", ".npy", ".zip", ".tar", ".tgz",
    ".tif", ".tiff", ".pem", ".key",
}
SKIP_PARTS = {".git", ".build", ".venv", "__pycache__", ".pytest_cache"}
TOKENS = [
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(rb"\bhf_[A-Za-z0-9]{25,}\b"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{25,}\b"),
    re.compile(rb"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----"),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []
    manifest = json.loads((ROOT / "handoff/SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        path = ROOT / row["path"]
        if not path.is_file():
            failures.append("missing-import: " + row["path"])
        elif sha(path.read_bytes()) != row["sha256"]:
            failures.append("changed-import: " + row["path"])

    files = [
        p for p in ROOT.rglob("*")
        if p.is_file() and not set(p.relative_to(ROOT).parts) & SKIP_PARTS
    ]
    python_count = 0
    for path in files:
        rel = path.relative_to(ROOT)
        if path.suffix.lower() in FORBIDDEN:
            failures.append("excluded-file-type: " + rel.as_posix())
        if path.name in {"completed.jsonl", "full_cases.json", ".env"}:
            failures.append("excluded-file-name: " + rel.as_posix())
        if path.stat().st_size >= 40 * 1024**2:
            failures.append("oversize-file: " + rel.as_posix())
        data = path.read_bytes()
        if path.suffix.lower() in {".pptx", ".docx"}:
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    data = b"\n".join(
                        z.read(n) for n in z.namelist()
                        if n.endswith((".xml", ".rels"))
                    )
            except zipfile.BadZipFile:
                failures.append("invalid-office-file: " + rel.as_posix())
        if path.suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg"}:
            if any(pattern.search(data) for pattern in TOKENS):
                failures.append("credential-pattern: " + rel.as_posix())
        if path.suffix == ".py":
            try:
                ast.parse(data.decode("utf-8-sig"), filename=rel.as_posix())
                python_count += 1
            except (UnicodeError, SyntaxError) as exc:
                failures.append(f"python-parse: {rel.as_posix()}: {type(exc).__name__}")

    tex_path = ROOT / "manuscripts/m03_jcde/01_manuscript/latex/main.tex"
    tex = tex_path.read_text(encoding="utf-8")
    author_line = next(line for line in tex.splitlines() if r"{\large Wei Xiong" in line)
    expected_authors = ["Wei Xiong", "Wei Meng", "Chu Qiu", "ShuWen Li", "Zhanhao Liang"]
    positions = [author_line.find(name) for name in expected_authors]
    if min(positions) < 0 or positions != sorted(positions):
        failures.append("current-author-order")
    if "Zhanhao Liang" not in tex or "mailto:lyon@cumt.edu.cn" not in tex:
        failures.append("second-corresponding-email")
    if "e-mail and ORCID required before submission" in tex:
        failures.append("author-placeholder")
    for target in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex):
        if not (tex_path.parent / target).is_file():
            failures.append("missing-figure: " + target)

    citekeys = set()
    for group in re.findall(r"\\[A-Za-z]*cite[A-Za-z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}", tex):
        citekeys.update(k.strip() for k in group.split(","))
    bibliography = (tex_path.parent / "references.bib").read_text(encoding="utf-8")
    bibkeys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bibliography))
    if len(citekeys) < 30 or citekeys - bibkeys:
        failures.append("citation-count-or-missing-bibkeys")

    gate = json.loads((M03 / "analysis/publication_evidence_gate.json").read_text(encoding="utf-8"))
    primary = list(csv.DictReader((M03 / "analysis/primary_sketch_tests.csv").open(encoding="utf-8")))
    if gate.get("q2_gate_passes") is not False or gate.get("primary_models_passing") != 0:
        failures.append("m03-frozen-negative-primary-gate")
    if len(primary) != 4 or any(float(r["p_holm"]) < 0.01 for r in primary):
        failures.append("m03-four-model-primary-tests")
    final = json.loads((M03 / "final_validation.json").read_text(encoding="utf-8"))
    if final.get("all_pass") is not True:
        failures.append("m03-historical-artifact-validation")

    summary = json.loads((M05 / "analysis/full_summary.json").read_text(encoding="utf-8"))
    result_bytes = (M05 / "full_results.csv").read_bytes()
    rows = list(csv.DictReader(io.StringIO(result_bytes.decode("utf-8"))))
    if len(rows) != 3405 or summary["row_count"] != len(rows):
        failures.append("m05-row-count")
    if summary["input_sha256"] != sha(result_bytes):
        failures.append("m05-result-summary-hash")

    report = {
        "status": "pass" if not failures else "fail",
        "imported_files_verified": len(manifest["files"]),
        "repository_files": len(files),
        "repository_bytes": sum(p.stat().st_size for p in files),
        "python_files_parsed": python_count,
        "m03_citekeys": len(citekeys),
        "m03_primary_models_passing": gate["primary_models_passing"],
        "m03_historical_artifact_validation": final["all_pass"],
        "m05_result_rows": len(rows),
        "m05_result_sha256": sha(result_bytes),
        "groups": dict(Counter(p.relative_to(ROOT).parts[0] for p in files)),
        "failures": failures,
        "scope": "Repository integrity and frozen-summary checks; no GPU or full-data replay.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.write_report:
        (ROOT / "handoff/VALIDATION.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
