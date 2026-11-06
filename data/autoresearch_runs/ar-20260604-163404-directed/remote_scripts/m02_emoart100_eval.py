#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import trimesh
from PIL import Image
from scipy.spatial.distance import jensenshannon
from transformers import CLIPModel, CLIPProcessor

from objaverse_gt_pipeline import canonicalize, render_mesh


EMOTIONS = ["Calm", "Excited", "Contentment", "Sad", "Alarmed", "Frustrated", "Happy", "Annoyed"]
PROMPTS = [f"a painting or 3D render that evokes {emotion.lower()} emotion" for emotion in EMOTIONS]


def entropy(values: np.ndarray) -> float:
    probs = np.asarray(values, dtype=float)
    probs = probs / max(probs.sum(), 1e-12)
    return float(-(probs * np.log(np.maximum(probs, 1e-12))).sum())


def clip_predict(paths, model, processor, text_features, device, prefix: str):
    rows = []
    for start in range(0, len(paths), 32):
        batch = paths[start : start + 32]
        images = [Image.open(path).convert("RGB") for path in batch]
        inputs = processor(images=images, return_tensors="pt").to(device)
        with torch.no_grad():
            features = model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
            probs = (100.0 * features @ text_features.T).softmax(dim=-1).cpu().numpy()
        for path, prob in zip(batch, probs):
            top = int(prob.argmax())
            record = {
                f"{prefix}_path": str(path),
                f"{prefix}_top_emotion": EMOTIONS[top],
                f"{prefix}_top_prob": float(prob[top]),
                f"{prefix}_entropy": entropy(prob),
            }
            for emotion, value in zip(EMOTIONS, prob):
                record[f"{prefix}_p_{emotion}"] = float(value)
            rows.append(record)
    return rows


def main() -> int:
    manifest = Path("/root/autodl-tmp/m03/datasets/emoart5k_m02_sample100/sample100_manifest.csv")
    run = Path("/root/autodl-tmp/m03/outputs/m02_emoart100/triposr_runs")
    out = Path("/root/autodl-tmp/m03/outputs/m02_emoart100/eval")
    render_dir = out / "renders"
    out.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(manifest)
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    mesh_map = {row["name"]: row["mesh"]["path"] for row in summary["results"] if row.get("ok")}

    render_rows = []
    for _, row in frame.iterrows():
        name = Path(row["input_png"]).stem
        mesh_path = mesh_map.get(name)
        png = render_dir / f"{name}.png"
        ok = False
        error = ""
        if mesh_path:
            try:
                mesh = trimesh.load(mesh_path, force="mesh")
                mesh, _ = canonicalize(mesh)
                render_mesh(mesh, png, size=512, view="iso")
                ok = True
            except Exception as exc:
                error = repr(exc)
        render_rows.append({**row.to_dict(), "name": name, "mesh_path": mesh_path, "render_path": str(png), "render_ok": ok, "render_error": error})

    render_frame = pd.DataFrame(render_rows)
    render_frame.to_csv(out / "render_manifest.csv", index=False)
    eval_frame = render_frame[render_frame["render_ok"].eq(True)].reset_index(drop=True)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id).to(device).eval()
    processor = CLIPProcessor.from_pretrained(model_id)
    text_inputs = processor(text=PROMPTS, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        text_features = model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    orig_preds = clip_predict([Path(path) for path in eval_frame["input_png"]], model, processor, text_features, device, "orig")
    render_preds = clip_predict([Path(path) for path in eval_frame["render_path"]], model, processor, text_features, device, "render")

    rows = []
    for (_, meta), orig, render in zip(eval_frame.iterrows(), orig_preds, render_preds):
        orig_probs = np.array([orig[f"orig_p_{emotion}"] for emotion in EMOTIONS], dtype=float)
        render_probs = np.array([render[f"render_p_{emotion}"] for emotion in EMOTIONS], dtype=float)
        gt = meta["dominant_emotion"]
        rows.append(
            {
                "request_id": meta["request_id"],
                "name": meta["name"],
                "dominant_emotion": gt,
                "valence": meta["valence"],
                "arousal": meta["arousal"],
                "input_png": meta["input_png"],
                "render_path": meta["render_path"],
                **orig,
                **render,
                "orig_matches_gt": bool(orig["orig_top_emotion"] == gt),
                "render_matches_gt": bool(render["render_top_emotion"] == gt),
                "render_matches_orig": bool(render["render_top_emotion"] == orig["orig_top_emotion"]),
                "js_render_to_orig": float(jensenshannon(orig_probs, render_probs, base=2.0) ** 2),
                "render_entropy_delta": float(render["render_entropy"] - orig["orig_entropy"]),
                "render_top_prob_delta": float(render["render_top_prob"] - orig["orig_top_prob"]),
            }
        )

    results = pd.DataFrame(rows)
    results.to_csv(out / "emoart100_affect_consistency.csv", index=False)
    aggregate = {
        "n": int(len(results)),
        "render_ok": int(render_frame["render_ok"].sum()),
        "orig_gt_match_rate": float(results["orig_matches_gt"].mean()),
        "render_gt_match_rate": float(results["render_matches_gt"].mean()),
        "render_orig_match_rate": float(results["render_matches_orig"].mean()),
        "js_render_to_orig_mean": float(results["js_render_to_orig"].mean()),
        "render_entropy_delta_mean": float(results["render_entropy_delta"].mean()),
        "render_top_prob_delta_mean": float(results["render_top_prob_delta"].mean()),
        "by_emotion": results.groupby("dominant_emotion")
        .agg(
            n=("request_id", "count"),
            orig_gt_match_rate=("orig_matches_gt", "mean"),
            render_gt_match_rate=("render_matches_gt", "mean"),
            render_orig_match_rate=("render_matches_orig", "mean"),
            js_render_to_orig_mean=("js_render_to_orig", "mean"),
        )
        .reset_index()
        .to_dict(orient="records"),
    }
    (out / "emoart100_affect_aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    print("WROTE", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

