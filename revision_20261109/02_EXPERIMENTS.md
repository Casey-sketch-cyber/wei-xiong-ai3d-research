# 02 实验方案（E1–E5）

总原则：已有的 6,240 个网格能复用就复用；只有 E2 和 E4 需要新推理，合计约 4 小时 GPU。所有新输出写到服务器：

```
/root/autodl-tmp/m03_q2_confirmatory_20260715/revision_20261109/
├── reeval/            # E1 重评估
├── render_aligned/    # E1 对齐后的六视角渲染
├── instantmesh_official_preproc/   # E2
├── input_cues.csv     # E3
├── lineart/           # E4 输入、推理与评估
└── qc/                # E5 对齐目检
```

冻结目录只读。下文的 `$ROOT` 指 `/root/autodl-tmp/m03_q2_confirmatory_20260715`，`$REV` 指 `$ROOT/revision_20261109`，`$EXP` 指仓库内 `experiments/m03_q2_confirmatory_20260715`。

---

## E1 三协议重评估（最优先）

### 目的

把姿态误差、尺度误差与形状误差分开，确认原结果有多少来自配准。

### 三种协议

| 协议 | 名称前缀 | 变换 | 回答的问题 |
| --- | --- | --- | --- |
| camera | `camera_` | 冻结的模型级尺度 + 轴矩阵，bbox 中心对齐（与原稿完全相同） | 不做任何逐样本校正时输出离真值多远 |
| rigid | `rigid_` | 在 camera 基础上逐样本搜索旋转 + 平移，尺度保持冻结值 | 去掉姿态误差后，尺度和形状还差多少 |
| sim | `sim_` | 逐样本旋转 + 平移 + 统一尺度 | 纯形状误差（领域常规做法） |

新论文的主终点改为 `sim` 协议（若关口 1 通过）。`camera` 与 `sim` 的差值、`align_sim_rotation_angle_deg`、`align_sim_scale` 构成新的“姿态/尺度保真度”终点，回应原稿“逐样本对齐会掩盖退化”的担心。

### 对齐算法（`alignment_core.py`，已实现并测试）

1. 在两个网格表面各采 6,000 点（哈希派生的固定种子）。
2. 候选旋转：单位阵 + 24 个立方体旋转 + 72 个固定种子（20261109）的随机旋转，共 96 个。
3. 粗配准：每个候选在 1,500 点子样本上跑 8 轮对称 ICP（双向最近邻对应，Umeyama 闭式解），sim 模式初始尺度取两点云 RMS 半径之比，尺度夹在 [0.25, 4]。
4. 精配准：粗配准最好的 5 个候选在 5,000 点上跑最多 50 轮，选全量点上对称 Chamfer 最小者。
5. 输出变换满足 `x_gt = s · x_pred · Rᵀ + t`，记录初始与对齐后 Chamfer、旋转角、尺度。

对称 ICP 的作用：自由尺度下，单向对应会把预测缩到目标的密集区域；双向对应可以避免这种塌缩。

合成测试（`tests/test_alignment_core.py`）覆盖：精确 Umeyama、随机旋转加 0.6–1.6 倍尺度恢复（旋转误差 < 0.4°，尺度误差 < 0.5%）、刚体模式保留尺度误差、模拟 M03 的倾斜视角、截掉部分几何的残缺预测。单次对齐约 2–3 秒。

### 指标

`reevaluate_aligned.py` 对每种协议计算（采样方式、随机种子、公式与冻结评估器完全一致）：

- F-score 在阈值 0.02、0.05、0.10、0.20 下的值，以及 precision、recall；
- Chamfer-L2、法向一致性；
- 体素 IoU 与体积比，分辨率 64 和 128（128 为冻结值；256 可选，较慢）；
- 各轴尺寸相对误差；
- 原始网格拓扑（与协议无关）。

### 步骤

1. **单元测试**：服务器上 `python -I experiments/m03_revision_20261109/tests/test_alignment_core.py`，6 项全部打印 PASS（不依赖 pytest）。
2. **小试（关口 1）**：每个模型、主实验、照片条件、前 20 个对象。

   ```bash
   for M in triposr instantmesh hunyuan21 trellis; do
     python -I experiments/m03_revision_20261109/reevaluate_aligned.py \
       --model $M \
       --inference-root $ROOT/inference \
       --deterministic-schedule $EXP/inference_schedule_deterministic.csv \
       --stochastic-schedule $EXP/inference_schedule_stochastic.csv \
       --frozen-calibration $ROOT/evaluation/$M/calibration.json \
       --output-root $REV/reeval_pilot \
       --split main --styles photo --object-limit 20
   done
   ```

   路径以服务器实际为准：先用 `ls $ROOT` 核对 `inference/` 与 `evaluation/` 的真实位置，冻结评估器读取的结果 JSON 是 `<inference-root>/<model>/<model>_results.json`。

3. **复现检查**：`merge_and_check.py` 指向小试目录，`camera_` 指标必须与冻结 CSV 逐条一致（误差 ≤ 1e-9）。不一致说明路径、校准文件或采样被改动，先查清再继续。
4. **关口 1 判断**：比较 `sim_voxel_iou_128` 与 `camera_voxel_iou_128` 的中位数，记录到 `revision_20261109/DECISIONS.md`。
5. **全量**：去掉 `--styles`、`--split`、`--object-limit`，每个模型用 `--shard k --num-shards 4` 并行。6,240 个任务、每个约 5–10 秒（两次对齐 + 三套指标），4 进程约 3–5 小时。
6. 合并并再次运行 `merge_and_check.py`，要求 `all_pass: true`。

### 对齐后的六视角渲染

`$EXP/render_diagnostics.py` 只做冻结变换。需要新增一个脚本 `render_diagnostics_aligned.py`（放在 `experiments/m03_revision_20261109/`）：

- 复用原脚本的渲染与比较函数（import，不复制修改原文件）；
- 读取 `reeval_results.csv` 中每个任务的 `align_sim_rotation/scale/translation`，在冻结变换之后再施加该变换；
- 只跑主实验的 5,040 个网格，输出列名与原 `render_diagnostics.csv` 相同，另加 `protocol=sim`。

### 验收

- 合成单元测试全过；
- `reproduction_check.json` 中 `all_pass: true`；
- 6,240 条记录 `reeval_status=success`，失败为 0，或每个失败都有错误文件并在 DECISIONS.md 中说明；
- 对齐后渲染 5,040 条全部成功。

---

## E2 InstantMesh 官方预处理核查

### 目的

排除“InstantMesh 在 sketch/edge 下崩溃是因为缺少官方预处理”的可能。

### 做法

1. 在服务器 InstantMesh 代码（冻结提交 `08822c5`）中阅读 `run.py` 和 `src/utils/infer_util.py`，确认官方推理时对输入图的处理。按本方案的了解，官方流程是先 `remove_background`（已有 alpha 时通常跳过）再 `resize_foreground(image, 0.85)`，但必须以该提交的实际代码为准，并把核对结果写进 DECISIONS.md。
2. 复制 `$EXP/run_instantmesh_confirmatory.py` 为 `experiments/m03_revision_20261109/run_instantmesh_official_preproc.py`，只在送入管线前加入与官方完全一致的预处理调用。其余参数（75 步、`instant-mesh-large`、种子）不变。
3. 新建调度表：主实验 6 种风格 × 120 对象 × 2 种子 = 1,440 个任务，`job_id` 与原表相同，输出到 `$REV/instantmesh_official_preproc/`。约 2 小时 GPU。
4. 用 `reevaluate_aligned.py` 评估（`--inference-root` 指向新目录；`--frozen-calibration` 仍用原 InstantMesh 校准，但因为预处理改变了物体在图中的大小，**只解读 `sim_` 和 `rigid_` 结果**，`camera_` 结果不进入论文）。

### 解读

- sketch/edge 的 `sim` 退化大幅减小：论文主结果改用官方预处理的 InstantMesh，原结果放进补充材料，并在讨论中写“预处理对鲁棒性的影响”这一发现。
- 变化不大：主结果保持原 InstantMesh 输出，E2 作为一段稳健性说明。

---

## E3 输入线索量

### 目的

把“近乎空白的素描”从弱点变成解释变量：退化是否集中在线索稀疏的输入上。

### 做法

```bash
python -I experiments/m03_revision_20261109/input_cue_stats.py \
  --schedule $EXP/inference_schedule_deterministic.csv \
  --output $REV/input_cues.csv
```

`inference_schedule_deterministic.csv` 覆盖全部 1,020 个唯一输入。E4 的新输入用 `--extra-inputs` 追加。

指标定义见脚本文档：墨迹覆盖率、前景平均亮度与标准差、前景-背景对比度、内部边缘密度（遮罩腐蚀 3 像素后，不计剪影轮廓）、前景面积比。

### 预先定义的稀疏输入

`ink_coverage < 0.05` 且 `edge_density < 0.02` 的输入记为“近乎空白”。这一阈值在看退化结果之前写入 DECISIONS.md，之后不再修改；分析时报告剔除这些输入前后的结果。

---

## E4 学习型线稿条件

### 目的

回应“五种风格都是 OpenCV 滤镜”的质疑，增加一个更接近手绘线稿的输入。

### 做法

1. 环境中安装 `controlnet_aux`（使用 hf-mirror），用 `LineartDetector.from_pretrained("lllyasviel/Annotators")`，`coarse=False`。
2. 输入：每个 C120 对象主视角的 `photo.png`，按 alpha 合成到白底，512×512。
3. 处理：检测器输出为黑底白线时取反为白底黑线；不做二值化；保存前附上原 alpha 遮罩（与其他风格一致）。条件名 `lineart`。
4. 可选 E4b：同样的线稿不附 alpha（让各模型自行抠图），条件名 `lineart_nomask`。只在时间允许时做。
5. 新调度表（新文件，格式与原表相同，`split=revision`）：TripoSR 120 个，其余三个模型各 120 × 2 种子。约 2 小时 GPU。
6. 用原有四个 `run_*_confirmatory.py` 推理（`--manifest` 指向新表，`--work` 指向 `$REV/lineart/`），再用 `reevaluate_aligned.py` 评估。配对基线是同一对象、同一种子的原 `photo` 输出。

### 留档

保存 10 个对象的 lineart 输入缩略图到仓库 `revision_20261109/assets/lineart_examples/`，用于论文图 1 和补充材料。

---

## E5 对齐目检

### 目的

确认对齐结果在视觉上合理，并识别旋转对称物体（瓶子、罐子等）的姿态角是否有意义。

### 做法

1. 用固定种子从全量结果中抽 40 个任务（四个模型 × 照片和 sketch × 5 个），另加 `sim` 对齐后 Chamfer 最大的 10 个任务。
2. 每个任务渲染一张三联图：真值、camera 协议下的预测、sim 协议下的预测，同一相机，叠加半透明真值轮廓。
3. 存到 `$REV/qc/`，并把拼图缩略版放进仓库 `revision_20261109/assets/alignment_qc.png`。
4. 在 DECISIONS.md 记录：明显对错的数量；对旋转对称物体，说明 `rotation_angle_deg` 只作描述，不作统计结论。

---

## 不做的事

- 不加新模型、不扩对象数、不做人评、不做任何模型微调。
- 不修改冻结脚本和冻结结果。
- 不根据结果调整 E3 的阈值或 E1 的对齐参数；如需调整，写明原因并同时报告调整前后的结果。
