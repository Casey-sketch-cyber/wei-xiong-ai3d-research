# AGENTS.md：给所有 AI 助手的项目说明

> Codex、Cursor、Claude、Grok 等所有 AI 工具在本项目工作前，必须先读完本文件。

## 项目概述

研究现成的 AI 图像补全模型修复受损画作时是否可信：把真实破损形状移植到 CC0 完好名画上，用多个开源补全模型修复，与原画比较，分画种、分破损报告"自然度"和"忠实度"。目标是一篇开源三区或四区期刊论文。

当前阶段：**写作**。两馆主实验和敏感性实验已完成（见 `docs/NATIVE_MAIN.md`、`docs/AIC_REPLICATION.md`、`docs/NATIVE_REVIEW.md`），真实形状分支仍受供体限制。

## 研究规则（所有 AI 必须遵守）

1. **不依赖人评。** 作者找不到评分人。任何设计都不能依赖人工打分、用户研究或专家评分；评价一律用原画作标准答案的自动指标。
2. **选题、文献树、创新点判断**按 [findInnovation 的 skill](https://github.com/Casey-sketch-cyber/findInnovation/blob/main/skills/research-innovation-points/SKILL.md) 执行，模板在 [findInnovation/templates](https://github.com/Casey-sketch-cyber/findInnovation/tree/main/templates)。
3. **写论文**时先读并遵守 [paperwrite 的写作 skill](https://github.com/Casey-sketch-cyber/paperwrite/blob/main/skills/research-paper-story-writing/SKILL.md)。
4. **文献必须核对。** 放进文献树或引用的每篇文献，都要打开原文页面核对标题、作者、年份和发表处；没核对的标"未核对原文"。不得编造文献、数据或实验结果。
5. **文献树版本不覆盖。** `docs/literature-tree/literature-tree-v1.md` 是 Claude 的草稿，只读；纠错写到 `literature/audit-of-claude-v1.md`，修订另起 v2。
6. **数据只用可公开的来源**：CC0 或明确允许研究使用的画作与破损标注；在 `docs/DECISIONS.md` 记录每个数据源的许可。图像、数据和模型权重不进 Git。

## 写作阶段分工（2026-11-21 起，作者确定）

| 工具 | 负责 | 不做 |
|---|---|---|
| Gemini | 按 [`docs/paper/WRITING_BRIEF.md`](docs/paper/WRITING_BRIEF.md) 重写论文正文，产出 `docs/paper/draft-v2.md` | 跑实验、改实验文档、自己补文献 |
| Codex | 配图（脚本在服务器生成，图像不进 Git）、文献检索与核对、新颖性检索、核对 Gemini 稿里的每个数字和引用 | 重写正文的故事和语气 |
| Claude | 审查所有 PR，合并或退回 | |

`docs/PAPER_DRAFT.md` 是 v1 初稿，只读。

## 技术栈

先导用 Python、PyTorch、Diffusers 和 LPIPS。算力为单张 RTX 3090（24 GB）。

## 环境与命令

见 [架构与先导运行命令](docs/ARCHITECTURE.md)。服务器上的数据、模型、环境、缓存、日志和输出均使用数据盘。

## 目录结构

```
docs/literature-tree/   文献树各版本
docs/PROGRESS.md        进度与待办
docs/DECISIONS.md       决策记录
docs/ARCHITECTURE.md    目录与数据流说明
literature/             检索记录、文献表、核查记录
experiments/            数据准备、模型推理、评分及分析
```

## 工作规则

1. **开始前**：先读 `docs/PROGRESS.md`、`docs/ARCHITECTURE.md`、`docs/DECISIONS.md`。
2. **分支与合并**：每个任务新建分支 `<工具名>/<任务简述>`（例如 `codex/verify-literature-tree`），做完后推送并创建 PR；不能创建 PR 时只推送分支也可以。**不要自己合并到 `main`，也不用等用户**：Claude 审查通过就合并，没通过就在 PR 里留言并在 `docs/PROGRESS.md` 的待办里登记原因。开工前先看有没有自己之前被退回的 PR，先把它改完。不要强制推送，不要改写已推送的历史。
3. **范围**：只改与当前任务相关的文件。
4. **依赖**：不要随意新增依赖；确实需要时，在提交说明里写明理由。
5. **安全**：不要提交密钥、`.env`、图像数据、模型权重、AI 工具的缓存或对话记录。
6. **验证**：提交前运行与改动相关的检查，并在 PR 里写明实际运行了什么。
7. **结束时**：更新 `docs/PROGRESS.md`；重要取舍写进 `docs/DECISIONS.md`。
8. **沟通**：始终用中文回复用户。

## 当前注意事项

- 旧的 M03 项目内容保存在分支 `archive/m03-ai3d-20261118` 和 `revision-20261109`，不要再往这两处提交。
- 仓库名还是旧名 `wei-xiong-ai3d-research`，以后可能改名；文档里的链接用相对路径。
