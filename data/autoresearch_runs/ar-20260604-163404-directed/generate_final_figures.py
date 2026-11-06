#!/usr/bin/env python
"""Generate final summary tables and figures for M03/M02 experiments."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "final_figures_tables"
STYLE_ORDER = ["edge", "flat", "low_detail", "sketch", "watercolor"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ordered(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_style = {str(row["style"]): row for row in rows}
    return [by_style[style] for style in STYLE_ORDER if style in by_style]


def m03_relative_table(rows: list[dict[str, object]], experiment: str) -> list[dict[str, object]]:
    out = []
    for row in ordered(rows):
        out.append(
            {
                "experiment": experiment,
                "style": row["style"],
                "n": row["n"],
                "chamfer_l2_delta_mean": row.get("chamfer_l2_delta_mean"),
                "fscore_0.05_delta_mean": row.get("fscore_0.05_delta_mean"),
                "fscore_0.1_delta_mean": row.get("fscore_0.1_delta_mean"),
                "pred_volume_ratio_mean": row.get("pred_volume_ratio_mean"),
                "pred_extent_z_ratio_mean": row.get("pred_extent_z_ratio_mean"),
                "pred_volume_wilcoxon_p": row.get("pred_volume_wilcoxon_p"),
                "pred_extent_z_wilcoxon_p": row.get("pred_extent_z_wilcoxon_p"),
                "vertices_ratio_mean": row.get("vertices_ratio_mean"),
                "faces_ratio_mean": row.get("faces_ratio_mean"),
            }
        )
    return out


def save_bar(ax, labels, values, title, ylabel, color):
    ax.bar(labels, values, color=color, edgecolor="#26313d", linewidth=0.7)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.28)
    ax.tick_params(axis="x", rotation=25)


def svg_bar_chart(
    path: Path,
    title: str,
    panels: list[dict[str, object]],
    width: int = 980,
    height: int = 420,
) -> str:
    panel_width = width // len(panels)
    top = 58
    bottom = 70
    chart_height = height - top - bottom
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2:.1f}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="#172033">{title}</text>',
    ]
    for idx, panel in enumerate(panels):
        labels = list(panel["labels"])  # type: ignore[index]
        values = [float(v) for v in panel["values"]]  # type: ignore[index]
        subtitle = str(panel["subtitle"])
        ylabel = str(panel.get("ylabel", ""))
        color = str(panel.get("color", "#4f8fc0"))
        baseline = panel.get("baseline")
        x0 = idx * panel_width + 46
        y0 = top
        inner_w = panel_width - 76
        inner_h = chart_height
        min_val = min([0.0, *values, float(baseline) if baseline is not None else 0.0])
        max_val = max([1.0, *values, float(baseline) if baseline is not None else 1.0])
        pad = (max_val - min_val) * 0.12 or 0.1
        min_val -= pad
        max_val += pad

        def y_for(v: float) -> float:
            return y0 + inner_h - ((v - min_val) / (max_val - min_val)) * inner_h

        parts.extend(
            [
                f'<text x="{x0 + inner_w / 2:.1f}" y="{y0 - 16}" text-anchor="middle" font-family="Arial" font-size="13" font-weight="700" fill="#172033">{subtitle}</text>',
                f'<line x1="{x0}" y1="{y0 + inner_h}" x2="{x0 + inner_w}" y2="{y0 + inner_h}" stroke="#27313c" stroke-width="1"/>',
                f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + inner_h}" stroke="#27313c" stroke-width="1"/>',
                f'<text x="{x0 - 32}" y="{y0 + inner_h / 2:.1f}" text-anchor="middle" transform="rotate(-90 {x0 - 32} {y0 + inner_h / 2:.1f})" font-family="Arial" font-size="11" fill="#5f6b7a">{ylabel}</text>',
            ]
        )
        for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
            val = min_val + (max_val - min_val) * frac
            y = y_for(val)
            parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + inner_w}" y2="{y:.1f}" stroke="#d8dee8" stroke-width="1"/>')
            parts.append(f'<text x="{x0 - 6}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="10" fill="#5f6b7a">{val:.2f}</text>')
        if baseline is not None:
            y = y_for(float(baseline))
            parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + inner_w}" y2="{y:.1f}" stroke="#7b2d26" stroke-width="1.2" stroke-dasharray="5,4"/>')
        gap = 8
        bar_w = max(16, (inner_w - gap * (len(labels) + 1)) / len(labels))
        zero_y = y_for(0.0)
        for i, (label, value) in enumerate(zip(labels, values)):
            x = x0 + gap + i * (bar_w + gap)
            y = y_for(value)
            rect_y = min(y, zero_y)
            rect_h = abs(zero_y - y)
            parts.append(f'<rect x="{x:.1f}" y="{rect_y:.1f}" width="{bar_w:.1f}" height="{rect_h:.1f}" fill="{color}" stroke="#26313d" stroke-width="0.7"/>')
            parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{rect_y - 5:.1f}" text-anchor="middle" font-family="Arial" font-size="10" fill="#172033">{value:.2f}</text>')
            parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y0 + inner_h + 18}" text-anchor="end" transform="rotate(-28 {x + bar_w / 2:.1f} {y0 + inner_h + 18})" font-family="Arial" font-size="10" fill="#172033">{label}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return str(path)


def make_svg_figures(tables: dict[str, list[dict[str, object]]], reason: str) -> list[str]:
    made = [f"matplotlib_unavailable: {reason}; generated SVG fallback figures"]
    main = tables["m03_main100"]
    styles = [str(row["style"]) for row in main]
    made.append(
        svg_bar_chart(
            OUT / "m03_main100_volume_z_ratios.svg",
            "M03 main100 geometry shrinkage",
            [
                {
                    "subtitle": "Volume ratio vs photo",
                    "ylabel": "ratio",
                    "labels": styles,
                    "values": [row["pred_volume_ratio_mean"] for row in main],
                    "baseline": 1.0,
                    "color": "#4f8fc0",
                },
                {
                    "subtitle": "Z-extent ratio vs photo",
                    "ylabel": "ratio",
                    "labels": styles,
                    "values": [row["pred_extent_z_ratio_mean"] for row in main],
                    "baseline": 1.0,
                    "color": "#d08a4c",
                },
            ],
        )
    )
    made.append(
        svg_bar_chart(
            OUT / "m03_main100_metric_paradox.svg",
            "M03 main100 metric paradox",
            [
                {
                    "subtitle": "Chamfer delta",
                    "ylabel": "style - photo",
                    "labels": styles,
                    "values": [row["chamfer_l2_delta_mean"] for row in main],
                    "baseline": 0.0,
                    "color": "#7aa66a",
                },
                {
                    "subtitle": "F-score@0.05 delta",
                    "ylabel": "style - photo",
                    "labels": styles,
                    "values": [row["fscore_0.05_delta_mean"] for row in main],
                    "baseline": 0.0,
                    "color": "#5e7bc0",
                },
                {
                    "subtitle": "Volume ratio",
                    "ylabel": "style / photo",
                    "labels": styles,
                    "values": [row["pred_volume_ratio_mean"] for row in main],
                    "baseline": 1.0,
                    "color": "#bd6f5a",
                },
            ],
            width=1320,
        )
    )
    res = tables["m03_res128"]
    res_styles = [str(row["style"]) for row in res]
    made.append(
        svg_bar_chart(
            OUT / "m03_res128_volume_z_ratios.svg",
            "M03 res128 robustness",
            [
                {
                    "subtitle": "Volume ratio vs photo",
                    "ylabel": "ratio",
                    "labels": res_styles,
                    "values": [row["pred_volume_ratio_mean"] for row in res],
                    "baseline": 1.0,
                    "color": "#4f8fc0",
                },
                {
                    "subtitle": "Z-extent ratio vs photo",
                    "ylabel": "ratio",
                    "labels": res_styles,
                    "values": [row["pred_extent_z_ratio_mean"] for row in res],
                    "baseline": 1.0,
                    "color": "#d08a4c",
                },
            ],
        )
    )
    proxy = tables["m02_proxy"]
    proxy_styles = [str(row["style"]) for row in proxy]
    made.append(
        svg_bar_chart(
            OUT / "m02_proxy_affect_drift.svg",
            "M02 proxy affect drift",
            [
                {
                    "subtitle": "Top emotion match",
                    "ylabel": "rate",
                    "labels": proxy_styles,
                    "values": [row["top_match_rate"] for row in proxy],
                    "baseline": 1.0,
                    "color": "#6f9f83",
                },
                {
                    "subtitle": "JS divergence",
                    "ylabel": "mean JS",
                    "labels": proxy_styles,
                    "values": [row["js_divergence_mean"] for row in proxy],
                    "baseline": 0.0,
                    "color": "#b97471",
                },
            ],
        )
    )
    emo = tables["m02_emoart_summary"][0]
    va = tables["m02_emoart_va"][0]
    made.append(
        svg_bar_chart(
            OUT / "m02_emoart50_affect_summary.svg",
            "M02 EmoArt-5k affect summary",
            [
                {
                    "subtitle": "Fine-label match",
                    "ylabel": "rate",
                    "labels": ["orig-GT", "render-GT", "render-orig"],
                    "values": [
                        emo["orig_gt_match_rate"],
                        emo["render_gt_match_rate"],
                        emo["render_orig_match_rate"],
                    ],
                    "baseline": 1.0,
                    "color": "#789bc0",
                },
                {
                    "subtitle": "Coarse affect audit",
                    "ylabel": "rate",
                    "labels": ["orig-GT valence", "render-GT valence", "render-orig arousal"],
                    "values": [
                        va["orig_valence_match_rate"],
                        va["render_valence_match_rate"],
                        va["render_orig_arousal_match_rate"],
                    ],
                    "baseline": 1.0,
                    "color": "#c68a54",
                },
            ],
        )
    )
    emo100 = tables["m02_emoart100_summary"][0]
    va100 = tables["m02_emoart100_va"][0]
    made.append(
        svg_bar_chart(
            OUT / "m02_emoart100_affect_summary.svg",
            "M02 EmoArt-100 affect robustness",
            [
                {
                    "subtitle": "Fine-label match",
                    "ylabel": "rate",
                    "labels": ["orig-GT", "render-GT", "render-orig"],
                    "values": [
                        emo100["orig_gt_match_rate"],
                        emo100["render_gt_match_rate"],
                        emo100["render_orig_match_rate"],
                    ],
                    "baseline": 1.0,
                    "color": "#789bc0",
                },
                {
                    "subtitle": "Coarse affect audit",
                    "ylabel": "rate",
                    "labels": ["orig-GT valence", "render-GT valence", "render-orig arousal"],
                    "values": [
                        va100["orig_valence_match_rate"],
                        va100["render_valence_match_rate"],
                        va100["render_orig_arousal_match_rate"],
                    ],
                    "baseline": 1.0,
                    "color": "#c68a54",
                },
            ],
        )
    )
    return made


def make_figures(tables: dict[str, list[dict[str, object]]]) -> list[str]:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on local environment
        return make_svg_figures(tables, str(exc))

    made: list[str] = []

    main = tables["m03_main100"]
    styles = [str(row["style"]) for row in main]
    volume = [float(row["pred_volume_ratio_mean"]) for row in main]
    zratio = [float(row["pred_extent_z_ratio_mean"]) for row in main]
    chamfer_delta = [float(row["chamfer_l2_delta_mean"]) for row in main]
    f05_delta = [float(row["fscore_0.05_delta_mean"]) for row in main]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    save_bar(axes[0], styles, volume, "M03 main100 volume ratio vs photo", "ratio", "#4f8fc0")
    axes[0].axhline(1.0, color="#7b2d26", linestyle="--", linewidth=1)
    save_bar(axes[1], styles, zratio, "M03 main100 z-extent ratio vs photo", "ratio", "#d08a4c")
    axes[1].axhline(1.0, color="#7b2d26", linestyle="--", linewidth=1)
    path = OUT / "m03_main100_volume_z_ratios.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    made.append(str(path))

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.1), constrained_layout=True)
    save_bar(axes[0], styles, chamfer_delta, "Chamfer delta", "style - photo", "#7aa66a")
    axes[0].axhline(0.0, color="#30343b", linewidth=1)
    save_bar(axes[1], styles, f05_delta, "F-score@0.05 delta", "style - photo", "#5e7bc0")
    axes[1].axhline(0.0, color="#30343b", linewidth=1)
    save_bar(axes[2], styles, volume, "Volume ratio", "style / photo", "#bd6f5a")
    axes[2].axhline(1.0, color="#7b2d26", linestyle="--", linewidth=1)
    path = OUT / "m03_main100_metric_paradox.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    made.append(str(path))

    res = tables["m03_res128"]
    styles_res = [str(row["style"]) for row in res]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    save_bar(
        axes[0],
        styles_res,
        [float(row["pred_volume_ratio_mean"]) for row in res],
        "M03 res128 volume ratio vs photo",
        "ratio",
        "#4f8fc0",
    )
    axes[0].axhline(1.0, color="#7b2d26", linestyle="--", linewidth=1)
    save_bar(
        axes[1],
        styles_res,
        [float(row["pred_extent_z_ratio_mean"]) for row in res],
        "M03 res128 z-extent ratio vs photo",
        "ratio",
        "#d08a4c",
    )
    axes[1].axhline(1.0, color="#7b2d26", linestyle="--", linewidth=1)
    path = OUT / "m03_res128_volume_z_ratios.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    made.append(str(path))

    proxy = tables["m02_proxy"]
    proxy_styles = [str(row["style"]) for row in proxy]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    save_bar(
        axes[0],
        proxy_styles,
        [float(row["top_match_rate"]) for row in proxy],
        "M02 proxy top emotion match",
        "rate",
        "#6f9f83",
    )
    axes[0].set_ylim(0, 1)
    save_bar(
        axes[1],
        proxy_styles,
        [float(row["js_divergence_mean"]) for row in proxy],
        "M02 proxy JS divergence",
        "mean JS",
        "#b97471",
    )
    path = OUT / "m02_proxy_affect_drift.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    made.append(str(path))

    emo = tables["m02_emoart_summary"][0]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    label_names = ["orig-GT", "render-GT", "render-orig"]
    label_vals = [
        float(emo["orig_gt_match_rate"]),
        float(emo["render_gt_match_rate"]),
        float(emo["render_orig_match_rate"]),
    ]
    save_bar(axes[0], label_names, label_vals, "EmoArt fine-label match", "rate", "#789bc0")
    axes[0].set_ylim(0, 1)
    va = tables["m02_emoart_va"][0]
    va_names = ["orig-GT valence", "render-GT valence", "render-orig arousal"]
    va_vals = [
        float(va["orig_valence_match_rate"]),
        float(va["render_valence_match_rate"]),
        float(va["render_orig_arousal_match_rate"]),
    ]
    save_bar(axes[1], va_names, va_vals, "EmoArt coarse affect audit", "rate", "#c68a54")
    axes[1].set_ylim(0, 1)
    path = OUT / "m02_emoart50_affect_summary.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    made.append(str(path))

    emo100 = tables["m02_emoart100_summary"][0]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    label_vals = [
        float(emo100["orig_gt_match_rate"]),
        float(emo100["render_gt_match_rate"]),
        float(emo100["render_orig_match_rate"]),
    ]
    save_bar(axes[0], label_names, label_vals, "EmoArt-100 fine-label match", "rate", "#789bc0")
    axes[0].set_ylim(0, 1)
    va100 = tables["m02_emoart100_va"][0]
    va_vals = [
        float(va100["orig_valence_match_rate"]),
        float(va100["render_valence_match_rate"]),
        float(va100["render_orig_arousal_match_rate"]),
    ]
    save_bar(axes[1], va_names, va_vals, "EmoArt-100 coarse affect audit", "rate", "#c68a54")
    axes[1].set_ylim(0, 1)
    path = OUT / "m02_emoart100_affect_summary.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    made.append(str(path))

    return made


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    m03_main_raw = load_json(ROOT / "m03_main100_metrics" / "eval_gt_relative_to_photo.json")
    m03_res_raw = load_json(ROOT / "m03_res128_metrics" / "eval_gt_relative_to_photo.json")
    m02_proxy_raw = load_json(ROOT / "m02_proxy_metrics" / "clip_affect_aggregate.json")
    m02_emo_raw = load_json(ROOT / "m02_emoart50_metrics" / "emoart50_affect_aggregate.json")
    m02_va_raw = load_json(ROOT / "m02_emoart50_metrics" / "emoart50_valence_arousal_aggregate.json")
    m02_emo100_raw = load_json(ROOT / "m02_emoart100_metrics" / "emoart100_affect_aggregate.json")
    m02_va100_raw = load_json(ROOT / "m02_emoart100_metrics" / "emoart100_valence_arousal_aggregate.json")

    tables = {
        "m03_main100": m03_relative_table(m03_main_raw, "m03_main100"),
        "m03_res128": m03_relative_table(m03_res_raw, "m03_res128"),
        "m02_proxy": ordered(m02_proxy_raw),
        "m02_emoart_by_emotion": m02_emo_raw["by_emotion"],
        "m02_emoart_summary": [
            {
                "n": m02_emo_raw["n"],
                "render_ok": m02_emo_raw["render_ok"],
                "orig_gt_match_rate": m02_emo_raw["orig_gt_match_rate"],
                "render_gt_match_rate": m02_emo_raw["render_gt_match_rate"],
                "render_orig_match_rate": m02_emo_raw["render_orig_match_rate"],
                "js_render_to_orig_mean": m02_emo_raw["js_render_to_orig_mean"],
                "render_entropy_delta_mean": m02_emo_raw["render_entropy_delta_mean"],
                "render_top_prob_delta_mean": m02_emo_raw["render_top_prob_delta_mean"],
            }
        ],
        "m02_emoart_va": [
            {
                "n": m02_va_raw["n"],
                "orig_valence_match_rate": m02_va_raw["orig_valence_match_rate"],
                "render_valence_match_rate": m02_va_raw["render_valence_match_rate"],
                "render_orig_valence_match_rate": m02_va_raw["render_orig_valence_match_rate"],
                "orig_arousal_match_rate": m02_va_raw["orig_arousal_match_rate"],
                "render_arousal_match_rate": m02_va_raw["render_arousal_match_rate"],
                "render_orig_arousal_match_rate": m02_va_raw["render_orig_arousal_match_rate"],
            }
        ],
        "m02_emoart100_by_emotion": m02_emo100_raw["by_emotion"],
        "m02_emoart100_summary": [
            {
                "n": m02_emo100_raw["n"],
                "render_ok": m02_emo100_raw["render_ok"],
                "orig_gt_match_rate": m02_emo100_raw["orig_gt_match_rate"],
                "render_gt_match_rate": m02_emo100_raw["render_gt_match_rate"],
                "render_orig_match_rate": m02_emo100_raw["render_orig_match_rate"],
                "js_render_to_orig_mean": m02_emo100_raw["js_render_to_orig_mean"],
                "render_entropy_delta_mean": m02_emo100_raw["render_entropy_delta_mean"],
                "render_top_prob_delta_mean": m02_emo100_raw["render_top_prob_delta_mean"],
            }
        ],
        "m02_emoart100_va": [
            {
                "n": m02_va100_raw["n"],
                "orig_valence_match_rate": m02_va100_raw["orig_valence_match_rate"],
                "render_valence_match_rate": m02_va100_raw["render_valence_match_rate"],
                "render_orig_valence_match_rate": m02_va100_raw["render_orig_valence_match_rate"],
                "orig_arousal_match_rate": m02_va100_raw["orig_arousal_match_rate"],
                "render_arousal_match_rate": m02_va100_raw["render_arousal_match_rate"],
                "render_orig_arousal_match_rate": m02_va100_raw["render_orig_arousal_match_rate"],
            }
        ],
    }

    for name, rows in tables.items():
        write_csv(OUT / f"{name}.csv", rows)

    experiment_summary = [
        {
            "experiment": "M03 main100",
            "scale": "100 objects x 6 styles",
            "completed_outputs": 600,
            "key_finding": "Style inputs shrink volume/thickness while Chamfer/F-score can improve.",
            "evidence": "m03_main100.csv; m03_main100_volume_z_ratios.svg",
        },
        {
            "experiment": "M03 res128 robustness",
            "scale": "30 objects x 6 styles",
            "completed_outputs": 180,
            "key_finding": "Volume and z-extent shrinkage persists at higher mesh extraction resolution.",
            "evidence": "m03_res128.csv; m03_res128_volume_z_ratios.svg",
        },
        {
            "experiment": "M02 proxy",
            "scale": "100 objects x 6 styles renders",
            "completed_outputs": 600,
            "key_finding": "Sketch has strongest affect-proxy drift; geometry and affect degradation differ.",
            "evidence": "m02_proxy.csv; m02_proxy_affect_drift.svg",
        },
        {
            "experiment": "M02 EmoArt-5k",
            "scale": "50 paintings",
            "completed_outputs": 50,
            "key_finding": "Painting-to-3D lowers fine emotion and valence proxy consistency.",
            "evidence": "m02_emoart_summary.csv; m02_emoart50_affect_summary.svg",
        },
        {
            "experiment": "M02 EmoArt-100 robustness",
            "scale": "100 paintings",
            "completed_outputs": 100,
            "key_finding": "The valence drop persists at 100 paintings, strengthening the proxy evidence.",
            "evidence": "m02_emoart100_summary.csv; m02_emoart100_affect_summary.svg",
        },
    ]
    write_csv(OUT / "experiment_summary_table.csv", experiment_summary)
    figure_captions = [
        {
            "figure": "m03_main100_volume_z_ratios.svg",
            "title": "M03 main100 geometry shrinkage",
            "caption": "Volume and z-extent ratios of TripoSR outputs under five stylized inputs relative to photo inputs on the curated Objaverse-100 benchmark. All styles reduce predicted mesh volume, and several styles strongly reduce z-extent, indicating style-induced geometric collapse.",
            "claim_link": "C-M03-1",
            "notes": "Main M03 evidence; use with m03_main100.csv.",
        },
        {
            "figure": "m03_main100_metric_paradox.svg",
            "title": "M03 main100 metric paradox",
            "caption": "Chamfer and F-score deltas are shown together with volume ratio. Several stylized inputs improve conventional point metrics relative to photo while producing smaller predicted volumes, revealing a mismatch between point-distance scores and 3D asset usability.",
            "claim_link": "C-M03-2",
            "notes": "Best central figure for the paper narrative.",
        },
        {
            "figure": "m03_res128_volume_z_ratios.svg",
            "title": "M03 res128 robustness",
            "caption": "A 30-object rerun with mc-resolution=128 preserves the volume and z-extent shrinkage pattern, suggesting that the main phenomenon is not solely caused by low-resolution mesh extraction.",
            "claim_link": "C-M03-3",
            "notes": "Robustness evidence, not full replacement for main100.",
        },
        {
            "figure": "m02_proxy_affect_drift.svg",
            "title": "M02 proxy affect drift",
            "caption": "CLIP affect-proxy drift on 600 rendered 3D outputs from the M03 main100 experiment. Sketch shows the lowest top-emotion match and highest JS divergence, while edge and low-detail are more affect-stable despite strong geometric degradation.",
            "claim_link": "C-M02-1",
            "notes": "Proxy only; do not present as human emotion judgment.",
        },
        {
            "figure": "m02_emoart50_affect_summary.svg",
            "title": "M02 EmoArt-5k affect summary",
            "caption": "Automatic affect-proxy results on 50 EmoArt-5k paintings converted to 3D. Fine-grained emotion match is low, while the coarse valence audit drops from original-vs-GT to render-vs-GT, suggesting that painting-to-3D conversion can weaken or re-encode affective cues.",
            "claim_link": "C-M02-2; C-M02-3",
            "notes": "CLIP zero-shot is weak on fine EmoArt labels; needs human validation.",
        },
        {
            "figure": "m02_emoart100_affect_summary.svg",
            "title": "M02 EmoArt-100 affect robustness",
            "caption": "A 100-painting EmoArt robustness run confirms the coarse valence drop: original-vs-GT valence match remains higher than render-vs-GT valence match after painting-to-3D conversion.",
            "claim_link": "C-M02-2; C-M02-3",
            "notes": "Automatic proxy robustness only; still needs human validation.",
        },
    ]
    write_csv(OUT / "figure_caption_table.csv", figure_captions)
    figures = make_figures(tables)
    manifest = {
        "tables": sorted(path.name for path in OUT.glob("*.csv")),
        "figures": sorted([path.name for path in OUT.glob("*.png")] + [path.name for path in OUT.glob("*.svg")]),
        "figure_generation_notes": figures,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
