# 论文图 1–5 的生成与核验

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
