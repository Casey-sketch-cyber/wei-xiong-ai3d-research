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
