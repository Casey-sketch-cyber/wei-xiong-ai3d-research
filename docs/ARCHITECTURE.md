# 架构说明

当前实现了先导的程序掩码分层部分。实验以固定的作品、掩码和模型版本为输入，保留每幅作品的多种子输出和自动评分。

## 目录结构

```
README.md
AGENTS.md                      所有 AI 的工作说明
CLAUDE.md                      指向 AGENTS.md
docs/
  literature-tree/
    literature-tree-v1.md      文献树 v1（Claude 起草，只读）
  ARCHITECTURE.md
  PROGRESS.md
  DECISIONS.md
literature/
  search-log.md                检索记录（只追加）
  papers.csv                   文献表
experiments/
  prepare_artworks.py          从馆方 API 核实许可、采集图像和编制清单
  models.py                    LaMa 和扩散补全模型的加载及推理
  run_pilot.py                 裁片、掩码、推理、评分及作品级分析
  run_followup.py              SDXL 敏感性和原尺度裁片先导
  patch_design.py              原像素取样与三类两档程序掩码
  additional_models.py        固定版本的 MAT 与 PowerPaint v1 适配
  diagnostic_metrics.py       掩码色差和局部 DISTS 追算
  analyze_followup.py         追加实验的同作品配对与分层汇总
  latent_mask_diagnostic.py   用旧输出诊断网格漏覆盖及分区亮度
  latent_aligned.py           扩张输入掩码并在原洞上合成
  run_latent_aligned.py       六组对齐重跑及共享输入对照
  analyze_aligned.py          修正前后同种子配对和四模型完整案例汇总
  analyze_official.py         SDXL 模型卡参数的同尺寸配对、分辨率及模型比较
  verify_official.py          核验模型卡运行产物及配对亮度偏移
```

## 计划中的数据流（草案，待定）

完好的 CC0 画作 → 移植真实破损形状（ARTeFACT 等）或按画材模拟破损 → 多个开源补全模型修复 → 与原画比较（忠实度、自然度、编造度）→ 分画种、分破损的统计与作图。

## 数据盘布局

在数据盘的项目目录下，`code/` 存运行代码，`data/` 存馆藏清单和输入原图，`models/` 存固定版本的模型权重，`cache/`、`venv/` 和 `tmp/` 存环境及缓存，`logs/` 存运行日志，`runs/` 存裁片、掩码、补全、评分和分析。图像和权重由数据盘管理。仓库记录代码、方法和聚合结果。

## 程序掩码流程

运行前将 `TMPDIR`、`XDG_CACHE_HOME`、`HF_HOME`、`TORCH_HOME` 和 `PIP_CACHE_DIR` 指向数据盘项目子目录。使用已有 CUDA PyTorch 环境，安装 Diffusers 0.35.2 和 LPIPS 0.1.4。LaMa 使用 IOPaint 发布的 TorchScript 权重并校验 SHA-256。扩散模型的版本见 `experiments/models.py`，将相应固定版本的 FP16 Safetensors 快照预取到 `$MODELS/huggingface`。扩散推理用 25 步、CFG 7.5、strength 1.0 及固定的通用绘画修复提示。

```bash
python -B experiments/prepare_artworks.py --output "$DATA" --exclude-id cma-121867
python -B experiments/run_pilot.py prepare --manifest "$DATA/artworks.csv" --run-dir "$RUN"
python -B experiments/run_pilot.py smoke --run-dir "$SMOKE" --models-dir "$MODELS" --model lama
python -B experiments/run_pilot.py smoke --run-dir "$SMOKE" --models-dir "$MODELS" --model sdxl
python -B experiments/run_pilot.py run --manifest "$DATA/artworks.csv" --run-dir "$RUN" --models-dir "$MODELS" --model lama
python -B experiments/run_pilot.py run --manifest "$DATA/artworks.csv" --run-dir "$RUN" --models-dir "$MODELS" --model sdxl
python -B experiments/run_pilot.py analyze --run-dir "$RUN" --model sdxl
```

技术验证先在合成图上运行。先导的 `prepared.json` 固定作品分组、清单哈希、裁片和掩码哈希。按作品、模型和种子保存 PNG 和评分，重跑时复用成功记录。分析输出 `summary.json` 和作品级 `artwork_scores.csv`。本次清单在采集模型输出前审查，排除了馆方标为画作但属于木门的藏品 `cma-121867`。

## 追加实验

`run_followup.py prepare-sensitivity` 以 `--baseline` 指向初版运行目录，在新的 `--run-dir` 中冻结同一裁片和掩码。`prepare-native` 接收初版 `--manifest`，在 `--data-dir` 下载馆方原图并在新 `--run-dir` 冻结 16 幅原尺度裁片和 96 个条件。用 `smoke` 和 `run` 子命令逐个指定模型与 `--models-dir`。

```bash
python -B experiments/run_followup.py prepare-sensitivity --baseline "$BASELINE" --run-dir "$SENSITIVITY"
python -B experiments/run_followup.py run --run-dir "$SENSITIVITY" --models-dir "$MODELS" --model sdxl_1024
python -B experiments/run_followup.py run --run-dir "$SENSITIVITY" --models-dir "$MODELS" --model sdxl_empty
python -B experiments/run_followup.py prepare-native --manifest "$DATA/artworks.csv" --data-dir "$NATIVE_DATA" --run-dir "$NATIVE"
python -B experiments/run_followup.py run --run-dir "$NATIVE" --models-dir "$MODELS" --model lama
```

原尺度运行的模型名为 `lama`、`sdxl`、`mat`、`powerpaint`。MAT 另用 timm 1.0.15 和固定版作者源码，权重和代码版本见 `additional_models.py`。PowerPaint 推荐独立数据盘环境（Diffusers 0.27.0、Transformers 4.40.2、Hugging Face Hub 0.25.2 和 Accelerate 0.34.2），使用固定的作者源码与两个替换权重并验证 SHA-256。SDK 缓存继续放在 `$MODELS/huggingface`。实际加载前依次对每个可用模型运行合成图验证。

`diagnostic_metrics.py --run-dir "$RUN" --output "$NEW_JSON"` 在输入目录之外补算诊断分，使用 scikit-image 0.25.2、DISTS-pytorch 0.1 及其固定 VGG16 权重。以 `analyze_followup.py --baseline "$BASE_SCORES" --sensitivity "$SENS_SCORES" --native "$NATIVE_SCORES" --native-plan "$NATIVE/prepared.json" --output "$SUMMARY"` 汇总。工作和数据清单相同的条件才进入同一配对分析。

## 潜空间网格修正

用 `latent_mask_diagnostic.py --run-dir "$OLD" --output "$DIAG"` 读取旧输出并记录逐输出及分条件的漏采统计。修正的 `prepare` 阶段校验并复制旧计划中的参考裁片与计分掩码，保存其哈希和新模型输入的面积。六个 `--arm` 见 `run_latent_aligned.py`。PowerPaint 继续使用独立环境。

```bash
python -B -m unittest -v experiments.test_latent_aligned
python -B experiments/run_latent_aligned.py prepare --arm baseline --reference "$BASELINE" --run-dir "$ALIGNED"
python -B experiments/run_latent_aligned.py smoke --arm baseline --model sdxl --models-dir "$MODELS" --run-dir "$SMOKE"
python -B experiments/run_latent_aligned.py run --arm baseline --model sdxl --models-dir "$MODELS" --run-dir "$ALIGNED"
python -B experiments/diagnostic_metrics.py --run-dir "$ALIGNED" --output "$ALIGNED_SCORE"
```

`analyze_aligned.py` 接收旧版、修正和共享输入的诊断评分 JSON。调用参数区分初版、敏感性和原尺度。原尺度分析另外读取旧 `prepared.json`，按画作及条件核对覆盖。

## SDXL 模型卡参数敏感性

在新的数据盘目录中运行 `official-baseline`、`official-1024` 和 `official-native`。三个组分别使用 `procedural-v1-qualified`、`sdxl-sensitivity-v1` 和 `native-v2` 的冻结计划。模型名分别为 `sdxl`、`sdxl_1024` 和 `sdxl`。运行计划记录模型卡三项参数，所有组用同一种子和原评分掩码。

```bash
python -B experiments/run_latent_aligned.py prepare --arm official-baseline --reference "$BASELINE" --run-dir "$NEW/official-baseline"
python -B experiments/run_latent_aligned.py smoke --arm official-baseline --model sdxl --models-dir "$MODELS" --run-dir "$SMOKE"
python -B experiments/run_latent_aligned.py run --arm official-baseline --model sdxl --models-dir "$MODELS" --run-dir "$NEW/official-baseline"
python -B experiments/diagnostic_metrics.py --run-dir "$NEW/official-baseline" --output "$NEW/diagnostics/official-baseline.json"
python -B experiments/verify_official.py --new-root "$NEW" --aligned-root "$ALIGNED_ROOT" --output "$NEW/diagnostics/verified-brightness.json"
```

三组均补齐诊断评分后运行核验。用 `analyze_official.py --help` 确认需传入同尺寸的历史网格修正评分、三组新评分、原输入和共享输入的像素模型评分及原尺度计划。[统计口径与上游设置](OFFICIAL_INFERENCE.md)
