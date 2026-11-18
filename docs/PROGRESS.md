# 项目进度（交接记录）

> 每个 AI 结束工作前在"工作记录"最上方追加一条，新的在上面。

## 当前状态

选题已定为"AI 补全模型修复画作的可信度评测"，文献树 v1 已起草，等待核查。没有实验代码。

## 待办

- [ ] 核查文献树 v1：用 LaMa、ARTeFACT、Shao 2023、Kachkine 2025、Rocafort 2025 的被引列表排查"未见跨画种系统评测"和"画作修复里未见编造度量"两个判断；纠错写到 `literature/audit-of-claude-v1.md`
- [ ] 核对 arXiv 条目的正式发表处，补进 `literature/papers.csv`
- [ ] 核对 ARTeFACT 许可（论文写 CC，Hugging Face 显示 afl-3.0）、其中画作样本数量，以及能否移植掩码并公开
- [ ] 统计 CC0 画作按画种的可得数量（大都会、芝加哥艺术博物馆、荷兰国立博物馆、美国国家美术馆、史密森尼）
- [ ] 找绘画修复伦理的原则性文献，补充或替换威尼斯宪章
- [ ] 在 3090 上实测候选补全模型的显存：LaMa、MAT、SDXL Inpainting、BrushNet 或 PowerPaint、FLUX.1 Fill
- [ ] 用 findInnovation 模板写 `docs/INNOVATION.md`

## 已知问题

- 本轮检索时，arXiv 批量接口和 OpenAlex 接口不可用，没有做被引列表排查。

---

## 工作记录

### 2026-11-18 · Claude · claude/painting-restoration-literature-tree
- **完成**：仓库改为新方向；旧 M03 内容保存到分支 `archive/m03-ai3d-20261118`；按 findInnovation skill 起草文献树 v1（三条脉络、文献表 36 条、难点—解法树、四种情况判断）；建立检索记录和文献表；补齐协作文档。
- **未完成**：被引列表排查；数据源许可核对；创新点评估文档。
- **注意 / 坑**：文献概括来自摘要页或对全文的检索摘录，没有通读全文；多数 arXiv 页面没写发表处。
