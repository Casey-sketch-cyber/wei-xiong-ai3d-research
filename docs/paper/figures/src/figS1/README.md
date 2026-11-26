# Figure S1 · 协议效应森林图

Claude 画，2026-11-26。数据只从 `docs/paper/peerj-cs/figdata/protocol_effects.csv` 读取（`metric == "mae"` 的 29 行），脚本里不写任何数值；分组 A–F 与 Table S2 一一对应。

```bash
python3 docs/paper/figures/src/figS1/make_figS1.py --fonts "$FIGGENIE/assets/fonts"
```

输出 `fig.pdf`（矢量、嵌入 Arimo 字体，与图 1–2 同为 Arial 度量）、`fig.png`（宽 3000 px，供 PeerJ 单独上传）和 `preview.png`。这些输出不进 Git，预览副本放在 `docs/paper/figures/previews/figure-S1-forest.png`。

设计：每组用独立横轴，因为各组效应相差两个数量级。灰带表示 ±0.01 MAE 实用阈值，虚线表示无差异。区间整体落在阈值带外的画实心蓝点，碰到阈值带的画空心灰点；除颜色外还用实心、空心区分，不只靠颜色。

## 图注（放进 Supplemental Article S1，紧跟 Table S2）

**Figure S1. Protocol and sensitivity effects on masked MAE.** Points show paired differences (comparison minus reference) and lines show their 95% bootstrap percentile intervals as reported in Table S2; n is the number of paired works. The grey band marks the pre-specified ±0.01 MAE practical margin, and the dashed line marks no difference. Filled blue markers denote intervals entirely outside the margin; open grey markers denote intervals that reach it. Each panel has its own horizontal scale. Panels A–F follow Table S2, which lists the reference groups, condition counts, secondary metrics and sources.
