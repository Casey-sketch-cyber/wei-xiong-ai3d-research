# M03 跨模型方向正式查新报告

日期：2026-07-14  
扫描对象：`paired stylised-input robustness + model x style interaction`  
原计划：复用 TripoSR 100 对象结果，新增 Hunyuan3D 2.1 的 100 对象双种子实验。

## 1. 结论

### 1.1 对当前 A 路线的判定

**判定：`NO-GO AS CLAIMED`。不建议把“跨模型风格鲁棒性”或
“model x style interaction”作为论文的主要创新点，也不建议按这个标题直接启动
100 对象扩展。**

原因不是实验做不出来，而是截至本次扫描，核心问题已被三组工作明显覆盖：

1. Cue3D 已在有真实 3D GT 的 GSO 和 Toys4K 上，对七个现代单图 3D 模型做了
   同对象受控线索扰动；其六种风格包括 line art、flat design、ink wash、oil
   painting 等，并明确比较不同模型家族的风格敏感性。
2. Kantarcı 等已用 3DCoMPaT++ 改变 2D 输入视角和风格，比较三个重建模型，并
   提出 part-level F1。它直接阻断“首个已知 GT 的跨风格多模型 benchmark”表述。
3. 2026 年 medieval manuscript miniatures 工作已在 69 幅真实艺术图像上比较七个
   image-to-3D 方法，并报告 depth-range ratio、watertight percentage 和 2AFC 人评。
   它阻断“首次在艺术输入上加入体积/拓扑诊断”的表述。

精确使用 `TripoSR + Hunyuan3D 2.1`，或者首次对这两个模型拟合混合效应模型，
属于实现与统计设计差异，不能单独支撑 SCI Q2 论文创新性。

### 1.2 仍然开放的窄方向

**判定：`PARTIAL-OPEN`。可保留的新问题不是“哪个模型更抗风格”，而是：**

> 在同对象、同视角、已知 3D GT 的反事实风格变化下，Chamfer 和 F-score 是否仍能
> 稳定地评价模型与输出？它们与 solid-geometry、topology 和 asset-readiness 指标的
> 排名一致性是否会随输入风格和模型家族系统性改变？

现有工作分别覆盖了线索鲁棒性、艺术图像多模型比较、人类质量评价和新 3D 指标，
但本次候选池中没有找到一个直接研究 **style-conditioned metric validity** 的工作：
即把输入风格作为条件，正式检验不同指标族的符号反转、模型排名反转和相关性失效。

这个空白只能支持“条件开放”，不能写成“确定没人做过”。数据库覆盖、索引延迟和
未公开稿件使绝对不存在无法被证明。

## 2. 检索方法与覆盖

- Semantic Scholar Graph API：14 条定向查询，年份过滤 2018--2026；14/14 成功。
- 去重后候选：1006 篇；自动相关度分数不低于 15 的候选 27 篇。
- 交叉来源：arXiv、NeurIPS Proceedings、CVF Open Access、Springer 版本页、
  IEEE DOI/元数据、作者主页和官方代码仓库。
- 全文下载并检视：Cue3D、Art3D、medieval manuscript miniatures、SI23DCQA。
- 另对 Eval3D、3DGen-Bench、SAUCD、DB-3DME、PAniC-3D 等读取官方摘要或版本页。

原始候选池见 `semantic_scholar_candidate_pool.csv/json`，逐查询状态见
`search_log.csv`，最近邻逐项比较见 `nearest_work_matrix.csv`。

## 3. 最强碰撞证据

### 3.1 Cue3D：对当前 A 路线构成直接碰撞

- 论文：NeurIPS 2025 Spotlight，`Cue3D: Quantifying the Role of Image Cues in
  Single-Image 3D Generation`。
- 设计：412 个 GSO、500 个 Toys4K 对象；每个对象有真实 3D GT；统一渲染。
- 模型：OpenLRM、SF3D、CRM、LGM、InstantMesh、Trellis、Hunyuan3D-2。
- 风格：ink wash、line art、pointillism、flat design、oil painting、sculpture。
- 其他扰动：shading、texture、silhouette、occlusion、edges、perspective、local
  continuity。
- 指标：多视角 2D 指标、整体 CD/F-score、visible-surface 指标和 symmetry。
- 结论：风格扰动显著降低性能，模型家族的敏感性不同，Hunyuan3D-2 等 native 3D
  方法总体更强、更稳。

因此，下列主张不能使用：

- “首个跨模型艺术风格鲁棒性研究”；
- “首次用同对象多风格和真实 GT 研究 image-to-3D”；
- “首次发现更强 3D 先验减少风格偏差”；
- “首次研究 model x style 差异”。

### 3.2 3DCoMPaT++ benchmark：早于 Cue3D 的直接前例

Kantarcı、Gökberk 和 Akarun 的 SIVP 论文使用 3DCoMPaT++，通过变化视角和 2D
输入风格测试三个重建模型，并用 part F1 识别细部和薄结构失败。虽然模型比当前
生成式 image-to-3D 系统旧，但“已知 GT + 风格变化 + 多模型 benchmark”结构已经
存在，不能把实验结构本身当作新贡献。

### 3.3 Manuscript miniatures：对体积和拓扑表述构成碰撞

该工作在 69 幅真实手稿人物上比较 TripoSR、SF3D、SPAR3D、TRELLIS、Wonder3D、
SAM 3D 和 Hi3DGen，报告 silhouette IoU、LPIPS、CLIP、depth-range ratio、
watertight rate，并用 26 名参与者完成 3686 个 2AFC trial。其缺点是没有真实 3D GT，
但它已经证明“艺术输入、多模型、深度/拓扑、人评”不是空白。

## 4. Claim-by-claim 判定

| 候选主张 | 判定 | 原因 |
|---|---|---|
| 同对象风格配对 benchmark | BLOCKED | Cue3D 与 SIVP benchmark 已覆盖 |
| 多模型风格鲁棒性比较 | BLOCKED | Cue3D 已覆盖七个现代模型 |
| 强 3D prior 减少风格退化 | BLOCKED | Cue3D 已报告 native 3D 方法的更强表现与鲁棒性 |
| 艺术输入的深度/拓扑诊断 | MOSTLY BLOCKED | 手稿研究已有 depth ratio 与 watertight rate |
| F-score 改善而体积塌缩 | PARTIAL-OPEN | 未找到完全相同的成对现象，但单一现象不足以独立成文 |
| 指标有效性随 style/model 改变 | PARTIAL-OPEN | 未找到直接检验 metric x style 排名稳定性的工作 |
| 新 3D 质量指标 | BLOCKED UNLESS VALIDATED | SAUCD、Eval3D、I3DQA、DB-3DME 已形成强前例 |

完整矩阵见 `claim_overlap_matrix.csv`。

## 5. 推荐的新论文命题

### 推荐英文题目

> Style-conditioned validity of geometry metrics for single-image-to-3D
> reconstruction: A paired multi-model study

更有冲突性的备选题目：

> When better surface scores hide worse solids: Metric rank reversals under
> stylised image-to-3D inputs

### 推荐中文命题

> 艺术化输入下单图三维重建指标是否仍然有效：一个关于表面分数、实体几何与模型
> 排名反转的成对多模型研究

### 允许写的三项贡献

1. 提出一个用于 **指标有效性审计** 的同对象反事实协议；配对设计是工具，不再声称
   是首创 benchmark。
2. 定量检验 CD/F-score、频谱/表面指标与 solid/topology 指标之间的符号反转和模型
   排名反转，并检验这种不一致是否受 style 和 model family 调节。
3. 给出不依赖单一新分数的报告规范：表面、实体、拓扑三类证据必须联合报告，并用
   bootstrap 区间明确不确定性。

## 6. 为什么现有 pilot 仍有价值

现有 TripoSR 主实验发现了明显的 F-score/volume disagreement；Hunyuan3D 2.1 pilot
又显示该现象不是简单地在强模型上按同样幅度重复。这两组结果可以成为新问题的
先验证据：**指标之间的不一致本身可能具有模型条件性。**

但 pilot 不能支持“所有现代 image-to-3D 模型都会体积塌缩”，也不能支持“Hunyuan
已解决问题”。Hunyuan 输出严格 watertight rate 只有 39.6%，说明实体几何评价必须
区分 signed volume、convex-hull envelope 与 topology validity。

## 7. 最终决策

- 当前 `model x style robustness` 题目：`NO-GO`。
- 直接运行 100 对象 Hunyuan 扩展：`HOLD`，本轮未启动。
- 新 `style-conditioned metric validity` 题目：`PARTIAL-OPEN`。
- 下一门：只有在用户选择该窄化命题后，先做 30 对象、三模型、可靠 solid GT 的
  metric-validity pilot；达到预注册门槛后才扩到 100 对象。

## 8. 主要一手来源

1. Cue3D: https://papers.neurips.cc/paper_files/paper/2025/hash/976cc04f0cbaad7790ce0d665e44f90f-Abstract-Conference.html
2. SIVP benchmark: https://link.springer.com/article/10.1007/s11760-024-03663-7
3. Manuscript miniatures: https://arxiv.org/abs/2604.08610
4. Art3D: https://arxiv.org/abs/2504.10466
5. Eval3D: https://openaccess.thecvf.com/content/CVPR2025/html/Duggal_Eval3D_Interpretable_and_Fine-grained_Evaluation_for_3D_Generation_CVPR_2025_paper.html
6. SI23DCQA: https://jhc.sjtu.edu.cn/~xiaohongliu/papers/2025SI23DCQA.pdf
7. IEEE TIP I3DQA paper: https://doi.org/10.1109/TIP.2026.3705200
8. SAUCD: https://openaccess.thecvf.com/content/CVPR2024/html/Luan_Spectrum_AUC_Difference_SAUCD_Human-aligned_3D_Shape_Evaluation_CVPR_2024_paper.html
9. 3DGen-Bench: https://arxiv.org/abs/2503.21745
10. DB-3DME: https://openaccess.thecvf.com/content/CVPR2026W/EvaGenFM/html/Jia_DB-3DME_From_Dataset_to_Benchmark_for_Human-aligned_Automatic_3D_Mesh_CVPRW_2026_paper.html

