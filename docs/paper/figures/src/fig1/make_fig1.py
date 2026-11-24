#!/usr/bin/env python3
"""Figure 1 (teaser): three protocol choices and the ordering under the controlled protocol.

Drawn by hand as SVG under the FigGenie contract (1 unit = 1 pt, one <g> per spec element) and checked with
FigGenie's check.py. Bitmaps (a_*.png, b_out_*.png) come from experiments/make_teaser_assets.py.

    FIGGENIE=<path to skills/figgenie-paper-diagram> python3 make_fig1.py   # writes spec.json and fig.svg here
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(os.environ["FIGGENIE"]) / "scripts"))
from place_text import place  # noqa: E402
from measure_text import width_of  # noqa: E402

FONT = "arial"
STACK = "Arimo, 'Liberation Sans', Arial, Helvetica, sans-serif"
W, H = 495, 226
S_BODY, S_TITLE, S_BIG = 6.5, 7.5, 9.0

INK, MUTED, RULE = "#262626", "#595959", "#A6A6A6"
RED, GREEN, GREEN_TXT, BLUE = "#C00000", "#70AD47", "#4E8A2E", "#4472C4"
BLUE_TINT, GREEN_TINT = "#DEEBF7", "#E2F0D9"
MODELS = [("LaMa", "#2F6FB5", "circle"), ("MAT", "#7FB2E0", "square"),
          ("PowerPaint v1", "#D9952B", "triangle"), ("SDXL", "#8A6FAE", "diamond")]

# The figure carries no explanatory text and no numbers (Peng Sida: a framework figure shows what is new;
# the text makes it understandable). The numbers live in the caption, with their sources:
# 59.5% of 1% crack pixels missed (NATIVE_APERTURE.md, 60 works); PowerPaint MAE -45% after alignment (40 works);
# luminance bias -0.085 / +0.055 / +0.034 (SDXL_PREFILL.md, 16 works x 6 losses); 281/360 and 350/360 scored.
PREFILL = [("black", "#000000", True), ("gray", "#808080", False), ("ring", None, False)]
CAPTION = ("Three protocol choices change what is measured when AI inpainting is scored on museum paintings. "
           "(a) Default 8x nearest-neighbour mask downsampling leaves part of a thin crack outside the model's mask "
           "(red; mean 59.5% of 1%-crack pixels across 60 Cleveland works). Grid alignment reaches every hole pixel "
           "and lowers PowerPaint masked MAE by about 45% over 40 complete paired works (240 conditions). "
           "(b) At SDXL strength 0.99, the mean signed luminance shifts for black, mid-gray and ring-mean prefill "
           "are -0.085, +0.055 and +0.034 over 16 works and six conditions per work. The tiles show one 5% broad-loss "
           "case, enlarged around the hole. "
           "(c) PowerPaint's safety checker withholds outputs (red) in 79 of 360 Cleveland and 10 of 360 Chicago "
           "conditions. (d) Under the controlled protocol, the masked-MAE ordering is the same in two museums, four "
           "media and six losses.")
COHORTS = [("CMA", 281, "78%"), ("AIC", 350, "97%")]


def tw(text, size, bold=False):
    return width_of(text, FONT, size, bold)[0] if text else 0.0


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=S_BODY, fill=INK, bold=False, anchor="start", extra=""):
    b = ' font-weight="bold"' if bold else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}"{b}{a}{extra}>{esc(s)}</text>'


def centred(s, box, size=S_BODY, fill=INK, bold=False):
    p = place(s, box, size=size, font=FONT, bold=bold)
    b = ' font-weight="bold"' if bold else ""
    return (f'<text x="{p["x"]:.2f}" y="{p["y"]:.2f}" font-size="{size}" fill="{fill}"{b} '
            f'text-anchor="middle">{esc(s)}</text>')


def marker(kind, cx, cy, r, fill):
    if kind == "circle":
        return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{fill}"/>'
    if kind == "square":
        return f'<rect x="{cx - r:.2f}" y="{cy - r:.2f}" width="{2 * r}" height="{2 * r}" fill="{fill}"/>'
    if kind == "triangle":
        return (f'<path d="M{cx:.2f} {cy - r * 1.1:.2f} L{cx + r * 1.1:.2f} {cy + r * 0.8:.2f} '
                f'L{cx - r * 1.1:.2f} {cy + r * 0.8:.2f} Z" fill="{fill}"/>')
    return (f'<path d="M{cx:.2f} {cy - r * 1.2:.2f} L{cx + r * 1.2:.2f} {cy:.2f} L{cx:.2f} {cy + r * 1.2:.2f} '
            f'L{cx - r * 1.2:.2f} {cy:.2f} Z" fill="{fill}"/>')


def verdict(cx, cy, ok):
    """A small disc with a tick or a cross (never colour alone)."""
    col = GREEN if ok else RED
    mark = (f'M{cx - 2.0:.2f} {cy:.2f} L{cx - 0.6:.2f} {cy + 1.5:.2f} L{cx + 2.2:.2f} {cy - 1.6:.2f}' if ok else
            f'M{cx - 1.6:.2f} {cy - 1.6:.2f} L{cx + 1.6:.2f} {cy + 1.6:.2f} M{cx + 1.6:.2f} {cy - 1.6:.2f} '
            f'L{cx - 1.6:.2f} {cy + 1.6:.2f}')
    return (f'<g data-symbol="verdict"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="3.6" fill="{col}" stroke="#FFFFFF" '
            f'stroke-width="0.6"/><path d="{mark}" fill="none" stroke="#FFFFFF" stroke-width="0.9" '
            f'stroke-linecap="round" stroke-linejoin="round"/></g>')


def image(x, y, w, h, href):
    return (f'<image x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" href="{href}"/>'
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" fill="none" stroke="{RULE}" stroke-width="0.5"/>')


def ring_colour():
    path = HERE / "ring_mean.json"
    return json.loads(path.read_text(encoding="utf-8"))["hex"] if path.exists() else "#9C8466"


def shield(cx, cy):
    s = 3.2
    return (f'<g data-symbol="shield"><path d="M{cx:.2f} {cy - s * 1.25:.2f} L{cx + s:.2f} {cy - s * 0.8:.2f} '
            f'L{cx + s:.2f} {cy + s * 0.1:.2f} Q{cx + s:.2f} {cy + s:.2f} {cx:.2f} {cy + s * 1.3:.2f} '
            f'Q{cx - s:.2f} {cy + s:.2f} {cx - s:.2f} {cy + s * 0.1:.2f} L{cx - s:.2f} {cy - s * 0.8:.2f} Z" '
            f'fill="none" stroke="{MUTED}" stroke-width="0.6" stroke-linejoin="round"/></g>')


def build():
    """2 x 2 grid: (a) mask alignment | (b) hole prefill / (c) withheld outputs | (d) model ordering."""
    nodes, edges, panels, annotations = [], [], [], []
    body = []
    CW, GAPX = 240, 15
    LX, RX = 0, CW + GAPX
    R1, R2 = 0, 114
    IMG = 11.5
    T, G = 74, 9

    # ---------------- (a) mask alignment ----------------
    xs = [LX + i * (T + G) for i in range(3)]
    tiles = [("a-crop", "", "a_crop.png", None), ("a-zoom-default", "default", "a_zoom_default.png", False),
             ("a-zoom-aligned", "aligned", "a_zoom_aligned.png", True)]
    assets = json.loads((HERE / "assets.json").read_text())
    zy, zx = assets["zoom_window_yx"]
    zw = assets["zoom_cells"] * 8
    k = T / 512
    for x, (nid, label, href, ok) in zip(xs, tiles):
        g = [image(x, R1 + IMG, T, T, href)]
        if label:
            lw = tw(label, S_BODY) + 9
            lx0 = x + (T - lw) / 2
            g += [verdict(lx0 + 3.6, R1 + 4.9, ok), text(lx0 + 9, R1 + 7.2, label, fill=MUTED)]
        body.append(f'<g id="n:{nid}" data-kind="node" data-role="{"novel" if ok else "existing"}" '
                    f'data-parent="a">{"".join(g)}</g>')
        nodes.append({"id": nid, "label": label, "kind": "image", "panel": "a",
                      "image": {"src": href, "role": "illustration" if label else "sample-input"}})
    sx, sy, sw = xs[0] + zx * k, R1 + IMG + zy * k, zw * k
    body.append(f'<g id="a:a-zoom" data-kind="annotation" data-anchor="a-crop">'
                f'<path d="M{sx + sw:.2f} {sy:.2f} L{xs[1]:.2f} {R1 + IMG:.2f} M{sx + sw:.2f} {sy + sw:.2f} '
                f'L{xs[1]:.2f} {R1 + IMG + T:.2f}" fill="none" stroke="{BLUE}" stroke-width="0.45" '
                f'stroke-dasharray="1.6 1.2"/></g>')
    annotations.append({"id": "a-zoom", "kind": "zoom", "text": "zoom", "anchor": "a-crop", "leader": True})

    # ---------------- (b) hole prefill ----------------
    bx = [RX + i * (T + G) for i in range(3)]
    body.append(f'<g id="a:b-sdxl" data-kind="annotation">'
                f'<text x="{RX + CW / 2:.2f}" y="{R1 + 7.2:.2f}" font-size="{S_BODY}" font-weight="bold" '
                f'fill="{BLUE}" text-anchor="middle">SDXL</text></g>')
    annotations.append({"id": "b-sdxl", "kind": "label", "text": "SDXL"})
    ring_fill = ring_colour()
    for x, (name, fill, bad) in zip(bx, PREFILL):
        fill = fill or ring_fill
        oid, href = f"b-out-{name}", f"b_out_{name}.png"
        frame = (f'<rect x="{x + 0.45:.2f}" y="{R1 + IMG + 0.45:.2f}" width="{T - 0.9}" height="{T - 0.9}" '
                 f'fill="none" stroke="{RED}" stroke-width="0.9"/>' if bad else "")
        inset = (f'<rect x="{x + 3:.2f}" y="{R1 + IMG + 3:.2f}" width="12" height="12" fill="{fill}" '
                 f'stroke="#FFFFFF" stroke-width="1"/>')
        body.append(f'<g id="n:{oid}" data-kind="node" data-role="output" data-parent="b">'
                    f'{image(x, R1 + IMG, T, T, href)}{frame}{inset}</g>')
        nodes.append({"id": oid, "label": "", "kind": "image", "panel": "b",
                      "image": {"src": href, "role": "sample-output"}})

    # ---------------- (c) withheld outputs ----------------
    cell, gap, cols, nrows = 3.2, 0.55, 18, 20
    ww = cols * (cell + gap) - gap
    wh = nrows * (cell + gap) - gap
    inner = 24
    x_first = LX + (CW - 2 * ww - inner) / 2
    title = "safety checker"
    t_w = tw(title, S_BODY)
    hx0 = LX + (CW - t_w - 9) / 2
    body.append(f'<g id="a:c-head" data-kind="annotation">{shield(hx0 + 3.2, R2 + 4.6)}'
                f'{text(hx0 + 9, R2 + 7.2, title, fill=MUTED)}</g>')
    annotations.append({"id": "c-head", "kind": "label", "text": title})
    for j, (name, ok, _pct) in enumerate(COHORTS):
        x0 = x_first + j * (ww + inner)
        y0 = R2 + IMG
        cells = "".join(
            f'<rect x="{x0 + (i % cols) * (cell + gap):.2f}" y="{y0 + (i // cols) * (cell + gap):.2f}" '
            f'width="{cell}" height="{cell}" fill="{"#D0D4DA" if i < ok else RED}"/>' for i in range(cols * nrows))
        body.append(f'<g id="n:c-waffle-{name.lower()}" data-kind="node" data-role="chart" data-parent="c" '
                    f'data-scale="data">{cells}'
                    f'{text(x0 + ww / 2, y0 + wh + 8.5, name, fill=MUTED, anchor="middle", extra=chr(32) + "data-label=" + chr(34) + "outside" + chr(34))}</g>')
        nodes.append({"id": f"c-waffle-{name.lower()}", "label": name, "kind": "chart", "panel": "c"})

    # ---------------- (d) model ordering: two lines that read like a sentence ----------------
    bh = 56
    by0 = R2 + IMG + (wh - bh) / 2
    body.append(f'<g id="c:d-box" data-kind="container" data-role="boundary">'
                f'<rect x="{RX}" y="{by0:.2f}" width="{CW}" height="{bh:.2f}" rx="3" fill="{GREEN_TINT}"/></g>')
    SYM = 18

    def line(items, cy, lead=None):
        widths = [tw(n, S_TITLE, True) + 17 for n, _, _ in items]
        total = sum(widths) + SYM * (len(items) - 1) + (SYM if lead else 0)
        x = RX + (CW - total) / 2
        syms = []
        if lead:
            syms.append(text(x + SYM / 2, cy + 3.2, lead, S_BIG, INK, True, "middle"))
            x += SYM
        for i, ((name, col, shape), w0) in enumerate(zip(items, widths)):
            nid = "d-" + name.split()[0].lower()
            body.append(f'<g id="n:{nid}" data-kind="node" data-role="module" data-parent="d">'
                        f'<rect x="{x:.2f}" y="{cy - 7:.2f}" width="{w0:.2f}" height="14" rx="2" fill="#FFFFFF" '
                        f'stroke="{RULE}" stroke-width="0.5"/>{marker(shape, x + 6.5, cy, 2.3, col)}'
                        f'{text(x + 11.5, cy + 2.7, name, S_TITLE, INK, True)}</g>')
            nodes.append({"id": nid, "label": name, "kind": "module", "panel": "d"})
            x += w0
            if i < len(items) - 1:
                syms.append(text(x + SYM / 2, cy + 3.2, "\u2248" if name == "LaMa" else "<", S_BIG, INK, True,
                                 "middle"))
                x += SYM
        return syms
    syms = line(MODELS[:2], by0 + bh * 0.33) + line(MODELS[2:], by0 + bh * 0.67, lead="<")
    body.append(f'<g id="a:d-order" data-kind="annotation">{"".join(syms)}</g>')
    annotations.append({"id": "d-order", "kind": "label", "text": "\u2248 < <"})

    # ---------------- captions, separators ----------------
    caps = [("a", "(a) Mask alignment", LX, R1 + 98), ("b", "(b) Hole prefill", RX, R1 + 98),
            ("c", "(c) Withheld outputs", LX, R2 + 107), ("d", "(d) Model ordering", RX, R2 + 107)]
    for pid, cap, x0, cy in caps:
        body.append(f'<g id="a:cap-{pid}" data-kind="annotation">'
                    f'{centred(cap, (x0, cy - 7, CW, 10), S_TITLE, INK, True)}</g>')
        annotations.append({"id": f"cap-{pid}", "kind": "label", "text": cap, "anchor": pid})
    xm = CW + GAPX / 2
    body.append(f'<line x1="{xm}" y1="2" x2="{xm}" y2="{H - 2}" stroke="{RULE}" stroke-width="0.5" '
                f'stroke-dasharray="2 1.6"/>')
    body.append(f'<line x1="2" y1="{R2 - 6}" x2="{W - 2}" y2="{R2 - 6}" stroke="{RULE}" stroke-width="0.5" '
                f'stroke-dasharray="2 1.6"/>')

    for pid, lab in (("a", "Mask alignment"), ("b", "Hole prefill"), ("c", "Withheld outputs"),
                     ("d", "Model ordering")):
        panels.append({"id": pid, "label": lab, "panel_label": f"({pid})", "axis": "narrative",
                       "order": "abcd".index(pid)})

    defs = (f'<defs><marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" '
            f'orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0 0.6 L5.4 3 L0 5.4 Z" '
            f'fill="{MUTED}"/></marker></defs>')
    # Preserve fractional glyph placement when Chromium exports print-size text.
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}pt" height="{H}pt" '
           'text-rendering="geometricPrecision" '
           f'font-family="{STACK}" font-size="{S_BODY}" data-spec="fig1-teaser" data-spec-version="3">'
           f'{defs}<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>{"".join(body)}</svg>')
    spec = {
        "meta": {"id": "fig1-teaser", "title": "Three protocol choices and the model ordering",
                 "family": "ai", "venue": "cvpr", "kind": "architecture", "column": "double", "width_pt": W,
                 "max_height_pt": H, "template": "ai", "direction": "mixed", "palette": "verdict-contrast",
                 "font": FONT, "step_markers": "none", "figure_kind": "comparison",
                 "caption_draft": CAPTION, "language": "en", "version": 3,
                 "ai": {"kinds": ["contribution-mosaic", "side-by-side-contrast"], "variant": "finding-cards",
                        "subfield": "vision", "subfield2": "generative", "arrangement": "panels-grid",
                        "grouping": ["whitespace", "tinted-regions"], "samples": "image",
                        "materials": ["frozen 512 crop of one 1% crack case (server archive)",
                                      "SDXL strength-0.99 outputs of one 5% broad-loss condition with black, mid-gray "
                                      "and ring-mean prefill, enlarged around the hole (server archive)"]}},
        "panels": panels, "containers": [{"id": "d-box", "label": "", "role": "boundary"}], "nodes": nodes,
        "edges": edges, "annotations": annotations, "legend": {"mode": "none"},
        "notes": "Pictures carry the message; numbers are in the caption only. ai.bare is deliberate (author rule: "
                 "the figure shows what is new, the text explains)."}
    return svg, spec


if __name__ == "__main__":
    svg, spec = build()
    (HERE / "fig.svg").write_text(svg)
    (HERE / "spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    print("wrote", HERE / "fig.svg")
