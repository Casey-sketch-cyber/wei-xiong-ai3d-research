# 论文配图

## 图 1–2（FigGenie）

| 图 | 可编辑源文件 | 审查预览 | 成图尺寸 |
| --- | --- | --- | --- |
| 1 · Teaser | [PPTX](figures/figure-1-teaser.pptx) | [PNG](figures/previews/figure-1-teaser.png) | 495 × 226 pt（通栏，2 × 2） |
| 2 · 方法流程 | [PPTX](figures/figure-2-pipeline.pptx) | [PNG](figures/previews/figure-2-pipeline.png) | 243 × 235 pt（单栏，两行蛇形） |

| 面板 | 冻结例图、来源与取样 |
| --- | --- |
| 1(a) 与图 2 | 沿用已发布掩码覆盖图的 1% 裂缝条件 `oil_wood_14_crack_01`。使用同幅画的槽位 14 裁片和六个逐像素核验的掩码，流程的对齐输入与 LaMa 合成来自 `oil_wood_14_crack_05`。图 1(a) 单例漏覆盖 52.9%，全队列 60 幅的平均为 59.54%。*Cottages Near Larchant*，Théodore Rousseau。[CMA 1915.728，CC0](https://www.clevelandart.org/art/1915.728) |
| 1(b) | 从原尺度 16 个 `_loss_05` 条件中，按 `SHA256("museum-painting-figures-v1|" + case_id)` 取首项 `watercolor_paper_02_loss_05`。黑色、中灰和环带三种输出使用同一 251 × 251 px 窗口（半开 `y0,x0,y1,x1 = 261,80,512,331`），覆盖完整计分洞。扩张洞外八像素环带的实测色为 `#CFCDBE`。图注的组级亮度仍按 16 幅 × 6 条件汇总。*Lighthouse Village (also known as Cape Elizabeth)*，Edward Hopper。[CMA 1930.851，CC0](https://www.clevelandart.org/art/1930.851) |

`make_teaser_assets.py --archive` 以既有图清单、两份冻结汇总及输出哈希定位素材，核验合成与预填色输出在原洞外保留原裁片像素。图形和文字在 PPTX 中可编辑，画作与模型输出保留为单独图片。图注供 Gemini 改写，以 [图 1 spec](figures/src/fig1/spec.json) 和 [图 2 spec](figures/src/fig2/spec.json) 的 `caption_draft` 为准。

在数据盘使用 FigGenie 固定版本 `c136a6aeefc6f6fe11fc615a5199cca57be3322a`，运行时 `python3` 需能导入 NumPy、Pillow、lxml、python-pptx、fontTools 和 Playwright，Chromium 的依赖放在数据盘。两张图 FigGenie lint 均为 0 错误。保留已审布局及短标签，图 2 的单栏蛇形流程按阶段框连线。色差指标在 PDF 中保留下标，FigGenie 转出的可编辑 PPTX 显示为同行的 ΔE00。

```bash
FIGGENIE="$FIGGENIE" FIGURE_ARCHIVE="$PROJECT" bash docs/paper/figures/src/build.sh
```

最新版 PDF、300 dpi PNG、自包含 SVG 与清单位于服务器项目数据盘的 `paper/figgenie-20261123/publication/`。清单 SHA-256 为 `c32fd464e5d87ef7d47b6df032a07dda741158ed297af7387a181425fea6387e`。风格参考图仍位于 `paper/figure-refs/`。

## 图 3–6（数据图）

| 图 | 文件名（PDF 与 PNG 共用） | 口径 |
| --- | --- | --- |
| 3 | `figure-3-examples` | 三种 5% 破损各一个冻结案例，按固定盐选取。每行统一放大范围，四模型格内标原洞 MAE。 |
| 4 | `figure-4-latent-coverage` | 三种 1% 破损各一个冻结案例，显示最近邻取样的漏覆盖和整格扩张。 |
| 5 | `figure-5-condition-mae` | 同馆、同条件下四模型共用可评分作品。点为绝对原洞 MAE 均值，区间为共同作品索引的 10,000 次 bootstrap 95% 百分位区间，纵轴为对数。 |
| 6 | `figure-6-powerpaint-coverage` | 两馆四组每组 90 个计划条件，砖红斜线为拦截，条内数字为可评分数与计划数。 |

```bash
MPLCONFIGDIR="$PROJECT/cache/matplotlib" "$PROJECT/venv/bin/python" -B experiments/make_paper_figures.py \
  --cma-root "$PROJECT/runs/native-main-20261120" \
  --aic-root "$PROJECT/runs/aic-replication-20261121" \
  --font-dir "$FIGGENIE/assets/fonts" \
  --output-dir "$PROJECT/paper/figures-3-to-6-20261121-arimo"
```

PDF、300 dpi PNG、联系表与清单位于以上数据盘目录，使用 495 pt 通栏和 FigGenie 的 Arimo 字体。清单 SHA-256 为 `69f5875429f4f35200f6c73a3287a0dbc0252a56e3ff37448b3c19c864cf625dd`。[统一样式](../../experiments/paper_style.mplstyle)

## 既有 Matplotlib 图（旧编号）

五张图从已核验的克利夫兰和芝加哥主实验档案生成。每张均有 PDF 和 300 dpi PNG。文件与图像清单都在服务器数据盘项目的 `paper/figures-20261121/`，生成日志在 `logs/paper-figures-20261121/render.log`。

| 图 | 文件名（PDF 与 PNG 共用） | 内容与分母 |
| --- | --- | --- |
| 1 | `figure-1-workflow` | 两馆取样、共享输入、原洞合成评分和计划分母 |
| 2 | `figure-2-examples` | 三类 5% 程序破损各一个 CC0 案例。每行依次显示冻结参考、二值原洞和四模型输出，采用同一细节范围 |
| 3 | `figure-3-latent-coverage` | 三类 1% 掩码的原洞、旧最邻近采样图与整格扩张图。保留单例漏覆盖比例及原洞外网格 |
| 4 | `figure-4-condition-mae` | 两馆各六种破损条件的原洞 MAE。同一馆同一条件下，四模型使用共同可评分作品 |
| 5 | `figure-5-powerpaint-coverage` | 两馆四组的 PowerPaint 可用输出占各自 90 个计划条件的比例。两馆均开启安全检查 |

图 2 从三个掩码家族各选一个不同的作品。规则是在 CC0、目标面积为 5%、四模型主设置均有保存输出的作品中，以固定盐 `museum-painting-figures-v1` 和条件 ID 的 SHA-256 排序依次选取。图 3 在面积为 1% 的条件中使用同样的选例规则。选例规则在生成图之前固定，用于说明个案。总体均值来自冻结的全样本比较。

| 图 2 条件 | 藏品与作者 | 开放记录 |
| --- | --- | --- |
| `oil_wood_02_crack_05` | *Portrait of a Woman*，Andrea del Sarto | [CMA 1944.92，CC0](https://www.clevelandart.org/art/1944.92) |
| `watercolor_paper_10_flake_05` | *Cherry Blossom Viewing at the Temple on Mt. Suribachi after a Design in Volume 5 of Picture Book of the Souvenirs of Edo (Ehon Edo miyage)*，Utagawa Hiroshige | [CMA 1985.295，CC0](https://www.clevelandart.org/art/1985.295) |
| `oil_wood_04_loss_05` | *Virgin and Child*，Lorenzo di Credi | [CMA 1916.826，CC0](https://www.clevelandart.org/art/1916.826) |

在数据盘的 Git 检出版本 `985d2c87d5817c2fb00ffa61347c03531e8f5740` 上生成，版本依赖为 NumPy、Pillow 和 Matplotlib（Agg）。输入目录及输出参数如下。

```bash
MPLCONFIGDIR="$PROJECT/cache/matplotlib" "$PROJECT/venv/bin/python" -B experiments/make_paper_figures.py \
  --cma-root "$PROJECT/runs/native-main-20261120" \
  --aic-root "$PROJECT/runs/aic-replication-20261121" \
  --output-dir "$PROJECT/paper/figures-20261121"
```

生成器逐一核对预定的两馆汇总哈希、原图、掩码及图 2 的四模型输出，记录完整注释和分母。已检查五个 PDF 的格式签名、PNG 尺寸与分辨率，并目视检查从服务器生成的联系表。清单为 `figure-manifest.json`，SHA-256 `ae3791716c3a9eaf7dbe6734876aa7a9cccf1e9fa155c8cfc529782e6b7d5326`。 [配图脚本](../../experiments/make_paper_figures.py)


### 2026-11-23 版面与 1(b) 选例修订（Claude）

- **版面**：作者认为两图太长（宽高比 3.5 和 4.2；FigGenie 统计的同类顶会图中位数为 2.1–2.7）。图 1 改为 2 × 2，宽高比 2.2；图 2 改为单栏两行，第二行从右向左，宽高比 1.0。
- **1(b) 选例规则**（先写定，再在服务器运行，不看结果挑图）：原例 `oil_canvas_03_flake_01` 的洞只占 1%，缩到 46 pt 后三种填色看不出差别。新规则只在 5% 广片缺失（`case_id` 以 `_loss_05` 结尾）的条件里，用同一盐值 `museum-painting-figures-v1` 取第一个。三张输出按三者有差异的像素（即生成的洞）求方形窗口，按洞的最大边长向两侧各加 35% 边距，窗口最小 96 px 并限制在裁片内。
- 通过 `FIGURE_ARCHIVE` 重建的预览和 PPTX 已使用新版布局与放大窗口。清单保留三个源输出和三张缩略图的哈希以及共同窗口坐标。
