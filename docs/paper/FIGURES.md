# 论文配图

## PowerPoint 布局草图（当前编号）

| 图 | 可编辑源文件 | 预览 | 成图尺寸 |
| --- | --- | --- | --- |
| 1 · Teaser | [PPTX](figures/figure-1-teaser.pptx) | [PNG](figures/previews/figure-1-teaser.png) | 17.4 × 7.15 cm |
| 2 · 方法流程 | [PPTX](figures/figure-2-pipeline.pptx) | [PNG](figures/previews/figure-2-pipeline.png) | 17.4 × 6 cm |

按 [配图设计说明](FIGURE_SPEC.md) 提交布局供审查。两图的文字、形状、箭头和方块图均可在 PowerPoint 中编辑。画作、模型输出和图标位置使用占位形状。用 python-pptx 1.0.2 生成，Microsoft PowerPoint 导出 PDF，Poppler 从 PDF 生成 180 dpi 预览。

```bash
python -B experiments/make_ppt_figures.py --output-dir docs/paper/figures
```

| 图中数字 | 对应实验证据 |
| --- | --- |
| 1(a) · 59.5% 与 −45% | 克利夫兰 60 幅的 1% 裂缝平均漏覆盖为 59.54%。PowerPaint 的原洞 MAE 在 40 幅六条件齐全的配对作品上从 0.1055 降至 0.0583，约降 45%，两组均开启安全检查。[全量原掩码对照](../NATIVE_APERTURE.md) |
| 1(b) · −0.085、+0.055、+0.034 | 固定 SDXL strength 0.99，16 幅 × 6 条件的掩码内平均亮度偏移。三值按黑色、中灰、环带均色排列，属于组级汇总。[SDXL 填色对照](../SDXL_PREFILL.md) |
| 1(c) · 281/360、350/360 | PowerPaint v1 安全检查开启时的两馆可用量。克利夫兰拦截 79，芝加哥拦截 10。[克利夫兰主实验](../NATIVE_MAIN.md) · [芝加哥复现](../AIC_REPLICATION.md) |
| 1(d) 与 2 | 排序仅概括共享扩张输入下的原洞 MAE。两馆各 60 幅、4 组各 15 幅、每幅 6 个条件，每馆每模型计划 360 条。流程图的 ΔE₀₀ 对应逐像素色差均值与掩码内平均 Lab 色的色差两种汇总。[克利夫兰主实验](../NATIVE_MAIN.md) · [芝加哥复现](../AIC_REPLICATION.md) |

风格参考位于服务器项目数据盘的 `paper/figure-refs/`，文件 `sources-20261121.json` 记录来源、尺寸与 SHA-256。六张参考图为 LDM 图 3、BrushNet 图 2 和图 3、PowerPaint 图 2、4K4D 图 2、MAT 图 8。参考缩略图仅供内部配图审查。

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
