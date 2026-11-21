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
W, H = 495, 172
S_BODY, S_TITLE, S_BIG = 6.5, 7.5, 9.0

INK, MUTED, RULE = "#262626", "#595959", "#A6A6A6"
RED, GREEN, GREEN_TXT, BLUE = "#C00000", "#70AD47", "#4E8A2E", "#4472C4"
BLUE_TINT, GREEN_TINT = "#DEEBF7", "#E2F0D9"
MODELS = [("LaMa", "#2F6FB5", "circle"), ("MAT", "#7FB2E0", "square"),
          ("PowerPaint v1", "#D9952B", "triangle"), ("SDXL", "#8A6FAE", "diamond")]

# Numbers (sources: NATIVE_APERTURE.md, SDXL_PREFILL.md, NATIVE_REVIEW.md, AIC_REPLICATION.md)
MISSED = "59.5%"                       # 1% cracks, 60 Cleveland works
PP_DROP = "−45%"                   # PowerPaint MAE, 40 paired works
PREFILL = [("black", "#000000", "−0.085", "0.151", True),
           ("mid-gray", "#808080", "+0.055", "0.130", False),
           ("ring mean", None, "+0.034", "0.098", False)]   # 16 works x 6 losses
CAPTION = ("Three protocol choices change what is measured when AI inpainting is scored on museum paintings. "
           "(a) Default 8x nearest-neighbour mask downsampling misses part of a 1% crack; a grid-aligned input reaches "
           "every hole pixel. (b) At SDXL strength 0.99 the hole's prefill colour shifts luminance bias and error. "
           "(c) PowerPaint's safety checker withholds outputs at different rates in two museums. (d) Under the "
           "controlled protocol the masked-MAE ordering is the same in both museums, four media and six losses.")
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


def shield(cx, cy):
    s = 3.2
    return (f'<g data-symbol="shield"><path d="M{cx:.2f} {cy - s * 1.25:.2f} L{cx + s:.2f} {cy - s * 0.8:.2f} '
            f'L{cx + s:.2f} {cy + s * 0.1:.2f} Q{cx + s:.2f} {cy + s:.2f} {cx:.2f} {cy + s * 1.3:.2f} '
            f'Q{cx - s:.2f} {cy + s:.2f} {cx - s:.2f} {cy + s * 0.1:.2f} L{cx - s:.2f} {cy - s * 0.8:.2f} Z" '
            f'fill="none" stroke="{MUTED}" stroke-width="0.6" stroke-linejoin="round"/></g>')


def build():
    nodes, edges, panels, annotations = [], [], [], []
    body = []

    # ---------------- panel (a): x 0-178 ----------------
    T, Y0 = 54, 11
    xs = [0, 62, 124]
    a_items = [("a-crop", "scoring mask", "a_crop.png"),
               ("a-zoom-default", "default: 8× nearest", "a_zoom_default.png"),
               ("a-zoom-aligned", "grid-aligned", "a_zoom_aligned.png")]
    assets = json.loads((HERE / "assets.json").read_text())
    zy, zx = assets["zoom_window_yx"]
    zw = assets["zoom_cells"] * 8
    k = T / 512
    sq = (xs[0] + zx * k, Y0 + zy * k, zw * k)
    for i, (nid, label, href) in enumerate(a_items):
        x = xs[i]
        if i:
            lw = tw(label, S_BODY) + 9
            lx0 = x + (T - lw) / 2
            g = [image(x, Y0, T, T, href), verdict(lx0 + 3.6, 4.9, i == 2),
                 text(lx0 + 9, 7.2, label, fill=MUTED)]
        else:
            g = [image(x, Y0, T, T, href), centred(label, (x - 4, 0.5, T + 8, 8.5), fill=MUTED)]
        body.append(f'<g id="n:{nid}" data-kind="node" data-role="{"existing" if i < 2 else "novel"}" '
                    f'data-parent="a">{"".join(g)}</g>')
        nodes.append({"id": nid, "label": label, "kind": "image", "panel": "a",
                      "image": {"src": href, "role": "illustration" if i else "sample-input"}})
    # zoom call-out from the crop to the default tile
    sx, sy, sw = sq
    body.append(f'<g id="a:a-zoom" data-kind="annotation" data-anchor="a-crop">'
                f'<path d="M{sx + sw:.2f} {sy:.2f} L{xs[1]:.2f} {Y0:.2f} M{sx + sw:.2f} {sy + sw:.2f} '
                f'L{xs[1]:.2f} {Y0 + T:.2f}" fill="none" stroke="{BLUE}" stroke-width="0.45" '
                f'stroke-dasharray="1.6 1.2"/></g>')
    annotations.append({"id": "a-zoom", "kind": "zoom", "text": "zoom", "anchor": "a-crop", "leader": True})

    # legend row under the tiles
    ly = 75.5
    parts, x = [], 0.0
    for sw_fill, sw_stroke, lab in ((GREEN, None, "reaches the model"), (RED, None, "missed"),
                                    ("none", BLUE, "latent cell")):
        st = f' stroke="{sw_stroke}" stroke-width="0.7"' if sw_stroke else ""
        parts.append(f'<rect x="{x:.2f}" y="{ly - 4.6:.2f}" width="4.6" height="4.6" fill="{sw_fill}"{st}/>')
        parts.append(text(x + 6.6, ly, lab, fill=MUTED))
        x += 6.6 + tw(lab, S_BODY) + 8
    body.append(f'<g id="legend" data-kind="legend">{"".join(parts)}</g>')

    # headline numbers
    hx = 0
    big_w = tw(MISSED, S_BIG, True)
    body.append(f'<g id="n:a-missed" data-kind="node" data-role="note" data-parent="a">'
                f'{text(hx, 93, MISSED, S_BIG, RED, True)}'
                f'{text(hx + big_w + 2.5, 93, "of 1% crack pixels missed by default", fill=INK)}</g>')
    nodes.append({"id": "a-missed", "label": f"{MISSED} of 1% crack pixels missed by default", "kind": "note",
                  "panel": "a"})
    body.append(f'<g id="n:a-gain" data-kind="node" data-role="note" data-parent="a">'
                f'{text(hx, 105, "grid-aligned input: PowerPaint MAE " + PP_DROP, fill=GREEN_TXT)}</g>')
    nodes.append({"id": "a-gain", "label": f"grid-aligned input: PowerPaint MAE {PP_DROP}", "kind": "note",
                  "panel": "a"})

    # ---------------- panel (b): x 189-339 ----------------
    bx = 189
    rows = [11, 45, 79]
    RT = 30
    sw_x, blk_x, blk_w, out_x, val_x = bx + 4, bx + 33, 40, bx + 83, bx + 117
    body.append(f'<g id="a:b-heads" data-kind="annotation">'
                f'{centred("prefill", (sw_x - 6, 0.5, 26, 8.5), fill=MUTED)}'
                f'{centred("output", (out_x - 6, 0.5, RT + 12, 8.5), fill=MUTED)}'
                f'{text(val_x, 7.2, "lum. bias", fill=MUTED)}</g>')
    annotations.append({"id": "b-heads", "kind": "label", "text": "prefill / SDXL output / bias"})
    ring_fill = "#9C8466"
    if (HERE / "ring_mean.json").exists():
        ring_fill = json.loads((HERE / "ring_mean.json").read_text())["hex"]
    blk_y0, blk_y1 = rows[0], rows[-1] + RT
    for (name, fill, bias, mae, bad), ry in zip(PREFILL, rows):
        fill = fill or ring_fill
        cy = ry + RT / 2
        nid = f"b-prefill-{name.split()[0]}"
        body.append(f'<g id="n:{nid}" data-kind="node" data-role="input" data-parent="b">'
                    f'<rect x="{sw_x:.2f}" y="{cy - 10:.2f}" width="14" height="14" fill="{fill}" stroke="{RULE}" '
                    f'stroke-width="0.5"/>{text(sw_x + 7, cy + 12.2, name, fill=MUTED, anchor="middle", extra=' data-label="outside"')}</g>')
        nodes.append({"id": nid, "label": name, "kind": "slot", "panel": "b"})
        body.append(f'<g id="e:{nid}-in" data-kind="edge" data-from="{nid}" data-to="b-sdxl" '
                    f'data-edge-kind="data"><path d="M{sw_x + 15.5:.2f} {cy - 3:.2f} H{blk_x - 1.6:.2f}" '
                    f'fill="none" stroke="{MUTED}" stroke-width="0.6" marker-end="url(#arrow)"/></g>')
        edges.append({"id": f"{nid}-in", "from": nid, "to": "b-sdxl", "kind": "data"})
        oid = f"b-out-{name.split()[0]}"
        href = f"b_out_{name.split()[0].replace('mid-gray', 'gray')}.png".replace("b_out_mid", "b_out_gray")
        href = {"black": "b_out_black.png", "mid-gray": "b_out_gray.png", "ring": "b_out_ring.png"}[name.split()[0]]
        frame = (f'<rect x="{out_x + 0.45:.2f}" y="{ry + 0.45:.2f}" width="{RT - 0.9}" height="{RT - 0.9}" fill="none" '
                 f'stroke="{RED}" stroke-width="0.9"/>' if bad else "")
        body.append(f'<g id="n:{oid}" data-kind="node" data-role="output" data-parent="b">'
                    f'{image(out_x, ry, RT, RT, href)}{frame}'
                    f'{text(val_x, cy - 1.2, bias, S_TITLE, RED if bad else INK, True, extra=' data-label="outside"')}'
                    f'{text(val_x, cy + 7.6, "MAE " + mae, fill=MUTED, extra=' data-label="outside"')}</g>')
        nodes.append({"id": oid, "label": f"{bias} MAE {mae}", "kind": "image", "panel": "b",
                      "image": {"src": href, "role": "sample-output"}})
        body.append(f'<g id="e:{oid}-in" data-kind="edge" data-from="b-sdxl" data-to="{oid}" '
                    f'data-edge-kind="data"><path d="M{blk_x + blk_w + 0.4:.2f} {cy:.2f} H{out_x - 1.8:.2f}" '
                    f'fill="none" stroke="{MUTED}" stroke-width="0.6" marker-end="url(#arrow)"/></g>')
        edges.append({"id": f"{oid}-in", "from": "b-sdxl", "to": oid, "kind": "data"})
    p1 = place("SDXL", (blk_x, blk_y0 + 30, blk_w, 10), size=S_TITLE, font=FONT, bold=True)
    body.append(f'<g id="n:b-sdxl" data-kind="node" data-role="novel" data-parent="b">'
                f'<rect x="{blk_x}" y="{blk_y0}" width="{blk_w}" height="{blk_y1 - blk_y0}" rx="3" '
                f'fill="{BLUE_TINT}" stroke="{BLUE}" stroke-width="0.6"/>'
                f'<text x="{blk_x + blk_w / 2:.2f}" y="{p1["y"]:.2f}" font-size="{S_TITLE}" font-weight="bold" '
                f'fill="{INK}" text-anchor="middle">SDXL</text>'
                f'{text(blk_x + blk_w / 2, p1["y"] + 11, "strength", fill=MUTED, anchor="middle")}'
                f'{text(blk_x + blk_w / 2, p1["y"] + 19.5, "0.99", fill=MUTED, anchor="middle")}</g>')
    nodes.append({"id": "b-sdxl", "label": "SDXL", "sublabel": "strength 0.99", "kind": "compute", "panel": "b"})

    # ---------------- panel (c): x 350-495 ----------------
    cx0, cw = 350, 145
    cell, gap, cols, nrows = 3.0, 0.6, 18, 20
    ww = cols * (cell + gap) - gap
    wgap = cw - 2 * ww
    title = "PowerPaint v1 safety checker"
    t_w = tw(title, S_BODY)
    hx0 = cx0 + (cw - t_w - 9) / 2
    body.append(f'<g id="a:c-head" data-kind="annotation">{shield(hx0 + 3.2, 4.6)}'
                f'{text(hx0 + 9, 7.2, title, fill=MUTED)}</g>')
    annotations.append({"id": "c-head", "kind": "label", "text": title})
    for j, (name, ok, pct) in enumerate(COHORTS):
        x0 = cx0 + j * (ww + wgap)
        y0 = 12.5
        cells = []
        for idx in range(cols * nrows):
            r, c = divmod(idx, cols)
            col = "#D0D4DA" if idx < ok else RED
            cells.append(f'<rect x="{x0 + c * (cell + gap):.2f}" y="{y0 + r * (cell + gap):.2f}" width="{cell}" '
                         f'height="{cell}" fill="{col}"/>')
        bottom = y0 + nrows * (cell + gap) - gap
        mid = x0 + ww / 2
        body.append(f'<g id="n:c-waffle-{name.lower()}" data-kind="node" data-role="chart" data-parent="c" '
                    f'data-scale="data">{"".join(cells)}'
                    f'{text(mid, bottom + 11.5, pct, S_BIG, INK, True, "middle", ' data-label="outside"')}'
                    f'{text(mid, bottom + 20.5, f"{name}: {ok}/360 scored", fill=MUTED, anchor="middle", extra=' data-label="outside"')}</g>')
        nodes.append({"id": f"c-waffle-{name.lower()}", "label": f"{pct} {name}: {ok}/360 scored", "kind": "chart", "panel": "c"})
    lx = cx0 + 34
    body.append(f'<g id="a:c-key" data-kind="annotation">'
                f'<rect x="{lx:.2f}" y="{112.4 - 3.2:.2f}" width="3.2" height="3.2" fill="#D0D4DA"/>'
                f'{text(lx + 5, 112.4, "scored", fill=MUTED)}'
                f'<rect x="{lx + 34:.2f}" y="{112.4 - 3.2:.2f}" width="3.2" height="3.2" fill="{RED}"/>'
                f'{text(lx + 39, 112.4, "withheld", fill=MUTED)}</g>')
    annotations.append({"id": "c-key", "kind": "label", "text": "scored / withheld"})

    # panel captions and separators
    caps = [("a", "(a) What the model is asked to fill", 0, 178),
            ("b", "(b) What fills the hole first", 189, 150),
            ("c", "(c) Which outputs get scored", 350, 145)]
    for pid, cap, x0, w0 in caps:
        body.append(f'<g id="a:cap-{pid}" data-kind="annotation">'
                    f'{centred(cap, (x0, 120.5, w0, 10), S_TITLE, INK, True)}</g>')
        annotations.append({"id": f"cap-{pid}", "kind": "label", "text": cap, "anchor": pid})
    for x in (183.5, 344.5):
        body.append(f'<line x1="{x}" y1="2" x2="{x}" y2="130" stroke="{RULE}" stroke-width="0.5" '
                    f'stroke-dasharray="2 1.6"/>')

    # ---------------- band (d) ----------------
    dy0, dh = 137, 34
    widths = [tw(n, S_TITLE, True) + 17 for n, _, _ in MODELS]
    SYM = 18
    total = sum(widths) + SYM * 3
    x = 176 + (W - 8 - 176 - total) / 2
    body.append(f'<g id="c:d-band" data-kind="container" data-role="boundary">'
                f'<rect x="0" y="{dy0}" width="{W}" height="{dh}" rx="3" fill="{GREEN_TINT}"/></g>')
    body.append(f'<g id="n:d-title" data-kind="node" data-role="note" data-parent="d">'
                f'{text(8, dy0 + 14.5, "(d) Under the controlled protocol", S_TITLE, INK, True)}'
                f'{text(8, dy0 + 24.5, "masked MAE \u00b7 2 museums \u00d7 4 media \u00d7 6 losses", fill=MUTED)}</g>')
    nodes.append({"id": "d-title", "label": "(d) Under the controlled protocol masked MAE \u00b7 2 museums \u00d7 4 media "
                  "\u00d7 6 losses", "kind": "note", "panel": "d"})
    syms = []
    for i, ((name, col, shape), w0) in enumerate(zip(MODELS, widths)):
        nid = "d-" + name.split()[0].lower()
        body.append(f'<g id="n:{nid}" data-kind="node" data-role="module" data-parent="d">'
                    f'<rect x="{x:.2f}" y="{dy0 + 10:.2f}" width="{w0:.2f}" height="14" rx="2" fill="#FFFFFF" '
                    f'stroke="{RULE}" stroke-width="0.5"/>{marker(shape, x + 6.5, dy0 + 17, 2.3, col)}'
                    f'{text(x + 11.5, dy0 + 19.7, name, S_TITLE, INK, True)}</g>')
        nodes.append({"id": nid, "label": name, "kind": "module", "panel": "d"})
        x += w0
        if i < 3:
            syms.append(text(x + SYM / 2, dy0 + 20.2, "\u2248" if i == 0 else "<", S_BIG, INK, True, "middle"))
            x += SYM
    body.append(f'<g id="a:d-order" data-kind="annotation">{"".join(syms)}</g>')
    annotations.append({"id": "d-order", "kind": "label", "text": "\u2248 < <"})

    for pid, lab in (("a", "What the model is asked to fill"), ("b", "What fills the hole first"),
                     ("c", "Which outputs get scored"), ("d", "Under the controlled protocol")):
        panels.append({"id": pid, "label": lab, "panel_label": f"({pid})", "axis": "narrative",
                       "order": "abcd".index(pid)})

    defs = (f'<defs><marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" '
            f'orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0 0.6 L5.4 3 L0 5.4 Z" '
            f'fill="{MUTED}"/></marker></defs>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}pt" height="{H}pt" '
           f'font-family="{STACK}" font-size="{S_BODY}" data-spec="fig1-teaser" data-spec-version="1">'
           f'{defs}<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>{"".join(body)}</svg>')
    spec = {
        "meta": {"id": "fig1-teaser", "title": "Three protocol choices and the ordering under the controlled protocol",
                 "family": "ai", "venue": "cvpr", "kind": "architecture", "column": "double", "width_pt": W,
                 "max_height_pt": H, "template": "ai", "direction": "left-right", "palette": "verdict-contrast",
                 "font": FONT, "step_markers": "none", "figure_kind": "comparison",
                 "caption_draft": CAPTION, "language": "en", "version": 1,
                 "ai": {"kinds": ["contribution-mosaic", "side-by-side-contrast"], "variant": "finding-cards",
                        "subfield": "vision", "subfield2": "generative", "arrangement": "panels-row",
                        "grouping": ["whitespace", "tinted-regions"], "samples": "image",
                        "materials": ["frozen 512 crop of one 1% crack case (server archive)",
                                      "SDXL strength-0.99 outputs of one condition with black, mid-gray and ring-mean "
                                      "prefill (server archive)", "numbers from the experiment reports"]}},
        "panels": panels, "containers": [{"id": "d-band", "label": "", "role": "boundary"}], "nodes": nodes, "edges": edges, "annotations": annotations,
        "legend": {"mode": "none"},
        "notes": "Teaser drawn with FigGenie conventions; numbers cited in docs/paper/FIGURE_SPEC.md."}
    return svg, spec


if __name__ == "__main__":
    svg, spec = build()
    (HERE / "fig.svg").write_text(svg)
    (HERE / "spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    print("wrote", HERE / "fig.svg")
