# M03 窄化方向预冻结协议：Style-conditioned Metric Validity

状态：`DRAFT-FROZEN / WAITING FOR USER CHOICE`  
本文件只定义下一步，不代表已启动实验。

## 1. 研究问题

在同一个真实 3D 对象、相同相机、相同模型参数下，仅改变输入视觉风格时：

1. CD 与 F-score 对输出质量的排序是否稳定？
2. 它们与实体占据、体积误差、深度覆盖和拓扑可用性的结论是否发生符号反转？
3. 指标不一致率是否随输入风格和模型家族显著变化？

## 2. 为什么不能直接复用原 100 个 Objaverse 对象作最终 GT

原集合中多数 source mesh 非 watertight，无法把 source signed volume 当作可靠真值。
旧论文可以比较 TripoSR 的 paired output volume，因为输出 watertight；新论文若要审计
指标有效性，则必须知道“哪个实体更接近 GT”，所以需要可靠的 solid reference。

推荐二选一：

- 从公开 GSO/Toys4K 中筛 30 个稳定、可体素化且拓扑检查通过的对象；或
- 对现有 Objaverse 集合建立可复核的 solid reference，但所有修复规则必须冻结，且
  repaired GT 与原 mesh 的表面偏差需要审计。

默认推荐第一种，避免把 mesh repair 误差引入核心结论。

## 3. Pilot 规模

- 对象：30。
- 输入：photo + edge + flat colour + low detail + sketch + watercolour，共 180 张。
- 模型：TripoSR、一个中等能力开放模型（优先 SF3D）、Hunyuan3D 2.1。
- 随机性：确定性模型 1 次；扩散模型 2 个冻结种子。
- PBR：不进入核心统计；只在最终论文选择 2--4 个案例展示。

## 4. 指标族

### 表面指标

- Chamfer distance。
- F-score@0.05 / 0.1。
- Normal consistency。
- SAUCD，若官方实现可稳定复现。

### 实体几何指标

- Voxel occupancy IoU against solid GT。
- Absolute solid-volume error against GT。
- x/y/z extent error 与 view-axis depth-coverage error。
- Convex-hull envelope error，仅作补充，不替代 solid volume。

### 拓扑与资产可用性

- Watertight rate。
- Connected-component count。
- Boundary/non-manifold edge count。
- Self-intersection proxy 或可稳定复现的 mesh validity check。
- Minimum-thickness proxy，仅在实现可复核时加入。

不建议在 pilot 阶段发明一个加权总分。先报告指标族之间的关系，避免权重任意性。

## 5. 统计检验

1. 对每个 metric 分别拟合 `metric ~ model * style + (1 | object)`，或使用配对层级
   bootstrap 给出同等可解释的区间。
2. 对每个 style 计算表面指标与实体/拓扑指标的 Kendall/Spearman 排名一致性。
3. 计算 sign-reversal rate：表面指标显示改善，但实体或拓扑指标显著恶化的比例。
4. 计算 model-rank reversal：模型排名在表面指标与实体指标之间发生互换的比例。
5. 所有置信区间按 object 聚类重采样，不能把同一对象的多 style/seed 当独立样本。

## 6. Pilot 通过门槛

满足以下至少两项，才扩到 100 对象：

1. 至少两个模型中出现预先定义的 sign reversal，且 95% cluster-bootstrap CI 不含 0。
2. 至少一种 style 下，表面与实体指标的模型排名发生稳定反转。
3. `metric family x style` 的差异具有中等以上效应，且不只由弱 photo baseline 驱动。
4. 现象在两个随机种子方向一致。

若只有 TripoSR 出现、Hunyuan 与 SF3D 均不出现，则不得写成跨模型规律；应停止扩展
或降级为单模型诊断/复现研究。

## 7. 100 对象扩展条件

通过 pilot 后再运行：

- 100 对象 x 6 输入 x 3 模型；扩散模型保留 2 seeds。
- 复用已有 TripoSR 输出前必须确认对象、相机与新 solid-GT 子集完全一致。
- 若对象集合改变，旧 100 对象结果只能作为外部复现，不得混入同一配对统计。
- 远程运行前生成不可变 manifest，记录 mesh hash、input hash、模型 commit、参数、
  seed、GPU 和包版本。

## 8. 当前停止点

本协议已冻结到可选择状态。未连接远程服务器，未下载新数据，未运行 30 对象 pilot，
也未启动原计划的 100 对象 Hunyuan 扩展。

