# 绘画数字修复：AI 补全模型在画作上可信吗

研究问题：现成的 AI 图像补全模型用来修复受损画作时，补出来的是原作的样子，还是"看起来合理、其实是编的"内容？在不同画种（油画、水彩、水墨、版画等）和不同破损（龟裂、剥落、污渍、缺失等）下，差别有多大？

做法设想（待文献树核查后定稿）：把真实破损的形状移植到 CC0 公开的完好名画上，用多个开源补全模型修复，再和原画逐项比较，把"自然度"和"忠实度"分开报告。原画就是标准答案，全程不需要人评。

> 本仓库原来是 M03（图像生成三维的跨风格鲁棒性）项目。2026-11-18 起改做本方向，旧内容完整保存在分支 [`archive/m03-ai3d-20261118`](../../tree/archive/m03-ai3d-20261118)。

## 从哪里看起

| 想做什么 | 看哪里 |
| --- | --- |
| 了解目前的判断 | [`docs/literature-tree/literature-tree-v1.md`](docs/literature-tree/literature-tree-v1.md)（Claude 起草，待核查） |
| 看检索过程和文献清单 | [`literature/search-log.md`](literature/search-log.md)、[`literature/papers.csv`](literature/papers.csv) |
| 看进度和待办 | [`docs/PROGRESS.md`](docs/PROGRESS.md) |
| 看为什么这样定 | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| AI 助手开工前 | [`AGENTS.md`](AGENTS.md) |

## 用到的共用方法

- 选题与创新点：[Casey-sketch-cyber/findInnovation](https://github.com/Casey-sketch-cyber/findInnovation)（改编自彭思达的选题方法）
- 论文写作：[Casey-sketch-cyber/paperwrite](https://github.com/Casey-sketch-cyber/paperwrite)
- 多 AI 协作规则：[Casey-sketch-cyber/ai-workflow](https://github.com/Casey-sketch-cyber/ai-workflow)
