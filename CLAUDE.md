# Claude 接续说明

请用中文与用户交流。这个仓库的任务是接续优化熊伟的 AI + 3D 研究内容；默认优先完善 M03。M02 和 M05 为独立方向，不能混写进 M03。

## 先读与证据优先级

1. handoff/CURRENT_STATE.md
2. handoff/CLAUDE_TASK.md
3. manuscripts/m03_jcde/01_manuscript/latex/main.tex
4. manuscripts/m03_jcde/05_evidence_audit/four-model-confirmatory-evidence-20260729-zh.md
5. experiments/m03_q2_confirmatory_20260715/CONFIRMATORY_PROTOCOL.md
6. experiments/m03_q2_confirmatory_20260715/results_final/artifacts_20260729/analysis/CONFIRMATORY_RESULTS_REPORT.md
7. experiments/m03_q2_confirmatory_20260715/results_final/artifacts_20260729/analysis/publication_evidence_gate.json
8. manuscripts/m03_jcde/04_reviews_revisions/jcde-official-sample-and-skill-analysis-zh.md

后期确认实验优先于早期 pilot、发现实验、旧主张矩阵和旧 RUN_INDEX。统计输出解释实验事实，写作和审核说明不能代替数值证据。

## M03 固定信息

- 作者顺序：Wei Xiong、Wei Meng、Chu Qiu、ShuWen Li、Zhanhao Liang。
- 第一通讯：Chu Qiu，appamm94@gmail.com。
- 第二通讯：Zhanhao Liang，lyon@cumt.edu.cn；目前没有 ORCID。
- Zhanhao Liang 为单位 3：School of Materials Science and Engineering, South China University of Technology, Guangzhou, China。
- Chu Qiu 为单位 4，原其他单位不变。
- 只在现有联系行保留 Chu Qiu 的 ORCID，不恢复此前删除的多人 ORCID 汇总段。
- 正文唯一编辑入口是 manuscripts/m03_jcde/01_manuscript/latex/main.tex，参考文献为同目录 references.bib。
- 现存 PDF 为 26 页、参考文献引用为 39 个 citekey，目标期刊为 JCDE。
- 作者贡献是已采用的暂定分工；不因排版或论文优化而凭空新增实质贡献。

## 不可被优化掉的证据

确认集有 120 个 GSO 对象，四模型为 TripoSR、InstantMesh、Hunyuan3D 2.1、TRELLIS，共 6,240 次重建。6,240 项完整性通过不等于研究假设通过。

预设 sketch robustness-gap 主检验：四模型经 Holm 校正后均未达到 0.01。publication_evidence_gate.json 的 q2_gate_passes 为 false；这不是期刊分区结论，而是早先自定的证据门槛未通过。

主叙事应报告模型与风格交互及模型特定的绝对退化，并透明保留主假设未确认的结果。F-score 阈值改为 0.10 后的敏感性、种子、视角、风格强度及模型例外也应保留。不能将探索性关联写成因果解释。

M02 的人评和正式 ArtEmis/WikiArt 授权实验没有完成。用户后续偏好不依赖真人评价、做小范围优化；不要把旧评分工具存在当作有真人结果。

M05 的结论限制为已编码几何可见性约束的后处理修复。476/480 和 hard-valid 只支持对应基准；不代表真实博物馆的美学、叙事体验、安全认证或全局最优。

## 写作与图表偏好

先核对证据和段落结构。写作按用户已指定的顺序：humanizer 起草，再用 20-ml-paper-writing 修改。相关文件：

- external/humanizer/SKILL.md
- external/AI-Research-SKILLs/20-ml-paper-writing/ml-paper-writing/SKILL.md
- external/nature-skills/skills/nature-figure/SKILL.md
- external/nature-skills/skills/nature-citation/SKILL.md

论文采用英文正文。图表优先使用真实实验素材与可编辑源文件。框架图只说明流程与诊断关系；整体统计结果独立展示。图片、网格和数值不得用生成模型重画成新的实验“证据”。

保留负结果和反例。参考文献不少于 30 条；新增文献要实际核验作者、题名、年份、DOI/正式页面与论点关系，不能以检索结果中的相似标题补造引用。

## 开发与交付

- 使用独立分支逐步优化，先记录审查问题，再做修改。
- 不把原始数据、完整生成结果、权重、缓存或凭据加入 Git。
- 远程路径和已知复现缺口见 handoff/REMOTE_STORAGE.md 与 handoff/LOCAL_SETUP.md。
- 本地实验脚本部分依赖原始 D: 路径、远程 /root/autodl-tmp 路径、GPU 和特定模型环境；先核对参数，不能把上传成功称作全量复现实验成功。
- 修改结果、图表或统计脚本时，同步正文与审核记录，保留原冻结结果。
- 交付前检查段落论证、期刊项目、全文格式与引文；重新编译并视觉检查受影响页面。
- 学术资源加速可在 AutoDL 终端使用 source /etc/network_turbo，Hugging Face 可用 hf-mirror.com。普通网络受影响时取消代理环境变量。不要在 Git 中记录代理凭据。
