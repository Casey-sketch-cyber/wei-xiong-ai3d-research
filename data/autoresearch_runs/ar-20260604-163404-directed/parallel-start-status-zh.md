# M03 / M02 并行启动状态

日期：2026-06-04  
Run ID：`ar-20260604-163404-directed`

## 总体安排

M03 作为 GPU 主线优先推进；M02 作为轻量研究线并行推进。  
原因：当前只有一张 RTX 5090，M03 的 image-to-3D baseline 和几何评价更需要 GPU；M02 目前更适合先做文献边界、数据表、指标和人工评价协议，不应抢 GPU。

## M03 当前状态

已完成：

- 远程服务器连接成功。
- GPU 确认：NVIDIA GeForce RTX 5090。
- PyTorch 确认：2.8.0+cu128。
- CUDA 可用：`torch.cuda.is_available() == True`。
- 计算能力：`(12, 0)`。
- 数据盘确认：`/root/autodl-tmp`，750GB 可用。
- 工作区创建：`/root/autodl-tmp/m03`。
- 远程脚本创建：
  - `/root/autodl-tmp/m03/scripts/bootstrap_m03.sh`
  - `/root/autodl-tmp/m03/scripts/env_probe.py`
  - `/root/autodl-tmp/m03/scripts/metric_smoke.py`
- 基础 metric 依赖安装成功：
  - scipy
  - scikit-image
  - trimesh
  - imageio
  - pandas
  - opencv-python-headless
  - tqdm
- 几何评价 smoke test 通过：
  - same-shape Chamfer：约 `0.0016`
  - scaled-shape Chamfer：约 `0.0339`

暂未完成：

- Stable Fast 3D / TripoSR 仓库克隆。

原因：

- 远程直接从 GitHub clone `stable-fast-3d` 卡住数分钟，只产生不完整 `.git` 内容。
- 已停止卡住的 git 进程，并清理不完整目录，未留下后台任务。

下一步：

1. 换用 GitHub zip / 镜像 / 本地下载后 scp 上传的方式获取 baseline 代码；
2. 优先跑通 TripoSR 或 Stable Fast 3D 的单图推理；
3. 如果 baseline 依赖 custom CUDA extension 且不支持 RTX 5090，立即换轻量替代 baseline；
4. 开始构建 30-object pilot。

## M02 当前状态

已完成：

- 建立 M02 并行计划文件：`m02-parallel-plan-zh.md`。
- 明确工作题目：
  - 中文：面向 AI 艺术资产生成的情感保持性评价：从二维绘画到三维风格化资产
  - 英文：Emotion-Preserving 2D-to-3D Art Asset Generation: Evaluating Affective Consistency from Paintings to Stylized 3D Assets
- 明确 novelty 边界：
  - 不抢 ArtEmis / EmoArt / AGSR 的 2D 艺术情感理解；
  - 不抢 Emo3D / EmoTaG / EMOCA 的 3D avatar 情感表达；
  - 保留“2D 绘画情感语义在通用 3D 艺术资产中的保持性”这个窄命题。
- 初步设计数据和指标：
  - ArtEmis / EmoArt / WikiArt / Objaverse；
  - emotion label consistency；
  - affective embedding similarity；
  - explanation evidence preservation；
  - multi-view affective stability；
  - human-model agreement。

下一步：

1. 建 ArtEmis / EmoArt 数据访问表；
2. 设计人工评价 rubric；
3. 准备一个 30 张画作的最小验证集；
4. 等 M03 pipeline 跑通后复用 3D 生成与渲染工具。

## 当前决策

- 主线：M03。
- 并行线：M02 先做设计与材料，不占 GPU。
- 远程服务器：可用。
- 最大风险：远程 GitHub clone 慢，baseline 获取方式要换。
