#!/usr/bin/env python
"""Generate a local browser-based rating tool for M02 human evaluation."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
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


def load_items() -> list[dict[str, str]]:
    with (ROOT / "annotation_items.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def page(items: list[dict[str, str]]) -> str:
    data = json.dumps(items, ensure_ascii=False)
    score_fields = json.dumps(SCORE_FIELDS)
    text_fields = json.dumps(TEXT_FIELDS)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>M02 Human Rating Tool</title>
<style>
  :root {{ --ink:#172033; --muted:#5f6b7a; --line:#d9e0e8; --panel:#fff; --bg:#f6f7f9; --accent:#1f6f8b; --ok:#2b7a4b; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:Arial, "Microsoft YaHei", sans-serif; color:var(--ink); background:var(--bg); }}
  header {{ position:sticky; top:0; z-index:5; background:rgba(255,255,255,.96); border-bottom:1px solid var(--line); padding:12px 20px; display:grid; grid-template-columns:1fr auto; gap:14px; align-items:center; }}
  h1 {{ margin:0; font-size:20px; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:flex-end; }}
  input, button, textarea {{ font-family:inherit; }}
  input[type=text] {{ border:1px solid var(--line); border-radius:6px; padding:8px 10px; min-width:180px; }}
  button {{ border:1px solid #b8c4ce; background:white; color:var(--ink); border-radius:6px; padding:8px 10px; cursor:pointer; }}
  button.primary {{ background:var(--accent); color:white; border-color:var(--accent); }}
  button:disabled {{ opacity:.45; cursor:not-allowed; }}
  main {{ max-width:1180px; margin:0 auto; padding:18px; }}
  .status {{ color:var(--muted); font-size:14px; }}
  .item {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; margin:16px 0; overflow:hidden; }}
  .item-head {{ display:flex; justify-content:space-between; gap:12px; padding:12px 14px; border-bottom:1px solid var(--line); }}
  .tags {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .tags span {{ background:#eef7fb; color:#285466; border:1px solid #c9d7df; border-radius:999px; padding:3px 8px; font-size:12px; }}
  .media {{ display:grid; grid-template-columns:1fr 1fr; gap:0; border-bottom:1px solid var(--line); }}
  figure {{ margin:0; padding:12px; border-right:1px solid var(--line); }}
  figure:last-child {{ border-right:0; }}
  img {{ width:100%; height:360px; object-fit:contain; background:#eef1f4; border:1px solid var(--line); }}
  figcaption {{ color:var(--muted); font-size:13px; padding-top:8px; }}
  .meta {{ display:grid; grid-template-columns:1fr 1fr; border-bottom:1px solid var(--line); }}
  .meta > div {{ padding:12px 14px; border-right:1px solid var(--line); }}
  .meta > div:last-child {{ border-right:0; }}
  h3 {{ margin:0 0 7px; font-size:14px; }}
  p {{ margin:0; color:var(--muted); line-height:1.5; font-size:14px; }}
  .ratings {{ padding:14px; display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:12px; }}
  .score-row {{ border:1px solid var(--line); border-radius:8px; padding:10px; }}
  .score-row label {{ display:block; font-weight:700; font-size:13px; margin-bottom:8px; }}
  .score-buttons {{ display:grid; grid-template-columns:repeat(5, 1fr); gap:6px; }}
  .score-buttons button.active {{ background:var(--ok); color:white; border-color:var(--ok); }}
  .text-grid {{ padding:0 14px 14px; display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:12px; }}
  textarea {{ width:100%; min-height:64px; border:1px solid var(--line); border-radius:6px; padding:8px; resize:vertical; }}
  .complete {{ color:var(--ok); font-weight:700; }}
  @media (max-width: 760px) {{ header {{ grid-template-columns:1fr; }} .controls {{ justify-content:flex-start; }} .media, .meta, .ratings, .text-grid {{ grid-template-columns:1fr; }} figure {{ border-right:0; }} img {{ height:280px; }} }}
</style>
</head>
<body>
<header>
  <div>
    <h1>M02 Human Rating Tool</h1>
    <div class="status" id="status">Loading...</div>
  </div>
  <div class="controls">
    <input id="annotator" type="text" placeholder="annotator_id, e.g. rater01">
    <button id="prev">Prev</button>
    <button id="next">Next</button>
    <button class="primary" id="export">Export CSV</button>
  </div>
</header>
<main id="app"></main>
<script>
const ITEMS = {data};
const SCORE_FIELDS = {score_fields};
const TEXT_FIELDS = {text_fields};
const STORAGE_KEY = "m02_human_rating_tool_v1";
let state = loadState();
let index = Number(state.index || 0);

function loadState() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}"); }}
  catch {{ return {{}}; }}
}}
function saveState() {{
  state.index = index;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  updateStatus();
}}
function itemRecord(id) {{
  state.records = state.records || {{}};
  state.records[id] = state.records[id] || {{}};
  return state.records[id];
}}
function escapeHtml(s) {{
  return String(s || "").replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[c]));
}}
function completeCount() {{
  return ITEMS.filter(it => SCORE_FIELDS.every(f => itemRecord(it.request_id)[f])).length;
}}
function updateStatus() {{
  const cc = completeCount();
  document.getElementById("status").innerHTML = `Item ${{index + 1}} / ${{ITEMS.length}} · complete ${{cc}} / ${{ITEMS.length}}`;
  document.getElementById("prev").disabled = index === 0;
  document.getElementById("next").disabled = index === ITEMS.length - 1;
}}
function setScore(requestId, field, value) {{
  itemRecord(requestId)[field] = String(value);
  saveState();
  render();
}}
function setText(requestId, field, value) {{
  itemRecord(requestId)[field] = value;
  saveState();
}}
function render() {{
  const it = ITEMS[index];
  const rec = itemRecord(it.request_id);
  const done = SCORE_FIELDS.every(f => rec[f]);
  const app = document.getElementById("app");
  const scoreLabels = {{
    emotion_preservation_1_5: "Emotion preservation",
    visual_evidence_preservation_1_5: "Visual evidence preservation",
    style_preservation_1_5: "Style preservation",
    geometry_usability_1_5: "Geometry usability",
    multiview_stability_1_5: "Multiview / asset stability",
    overall_acceptability_1_5: "Overall acceptability"
  }};
  app.innerHTML = `
    <section class="item">
      <div class="item-head">
        <div><strong>#${{String(it.item_index).padStart(2, "0")}}</strong> ${{escapeHtml(it.request_id)}} ${{done ? '<span class="complete">complete</span>' : ''}}</div>
        <div class="tags"><span>${{escapeHtml(it.dominant_emotion)}}</span><span>${{escapeHtml(it.valence)}}</span><span>${{escapeHtml(it.arousal)}}</span></div>
      </div>
      <div class="media">
        <figure><img src="${{escapeHtml(it.original_image)}}"><figcaption>Original painting</figcaption></figure>
        <figure><img src="${{escapeHtml(it.render_image)}}"><figcaption>TripoSR 3D render</figcaption></figure>
      </div>
      <div class="meta">
        <div><h3>Description</h3><p>${{escapeHtml(it.description)}}</p></div>
        <div><h3>Emotional impact</h3><p>${{escapeHtml(it.emotional_impact)}}</p></div>
      </div>
      <div class="ratings">
        ${{SCORE_FIELDS.map(field => `
          <div class="score-row">
            <label>${{scoreLabels[field]}}</label>
            <div class="score-buttons">
              ${{[1,2,3,4,5].map(v => `<button type="button" class="${{rec[field] == v ? 'active' : ''}}" onclick="setScore('${{it.request_id.replace(/'/g, "\\\\'")}}','${{field}}',${{v}})">${{v}}</button>`).join("")}}
            </div>
          </div>
        `).join("")}}
      </div>
      <div class="text-grid">
        ${{TEXT_FIELDS.map(field => `
          <label><h3>${{field}}</h3><textarea oninput="setText('${{it.request_id.replace(/'/g, "\\\\'")}}','${{field}}',this.value)">${{escapeHtml(rec[field] || "")}}</textarea></label>
        `).join("")}}
      </div>
    </section>`;
  updateStatus();
}}
function csvEscape(s) {{
  const v = String(s ?? "");
  return /[",\\r\\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
}}
function exportCsv() {{
  const annotator = document.getElementById("annotator").value.trim() || "rater";
  const fields = ["annotator_id","item_index","request_id","dominant_emotion",...SCORE_FIELDS,...TEXT_FIELDS];
  const rows = [fields.join(",")];
  for (const it of ITEMS) {{
    const rec = itemRecord(it.request_id);
    const row = {{
      annotator_id: annotator,
      item_index: it.item_index,
      request_id: it.request_id,
      dominant_emotion: it.dominant_emotion,
      ...rec
    }};
    rows.push(fields.map(f => csvEscape(row[f] || "")).join(","));
  }}
  const blob = new Blob([rows.join("\\r\\n") + "\\r\\n"], {{type:"text/csv;charset=utf-8"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `annotation_${{annotator}}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}}
document.getElementById("prev").onclick = () => {{ index = Math.max(0, index - 1); saveState(); render(); }};
document.getElementById("next").onclick = () => {{ index = Math.min(ITEMS.length - 1, index + 1); saveState(); render(); }};
document.getElementById("export").onclick = exportCsv;
document.getElementById("annotator").oninput = saveState;
render();
</script>
</body>
</html>
"""


def main() -> int:
    items = load_items()
    output = ROOT / "rating_tool.html"
    output.write_text(page(items), encoding="utf-8")
    print(json.dumps({"status": "ok", "items": len(items), "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

