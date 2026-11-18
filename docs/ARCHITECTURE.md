# 架构说明

当前只有调研文档，没有代码。实验设计定稿后再补充模块和数据流。

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
```

## 计划中的数据流（草案，待定）

完好的 CC0 画作 → 移植真实破损形状（ARTeFACT 等）或按画材模拟破损 → 多个开源补全模型修复 → 与原画比较（忠实度、自然度、编造度）→ 分画种、分破损的统计与作图。

## 外部依赖与服务

待定。候选：Hugging Face 上的开源补全模型；大都会博物馆等 CC0 图像接口；ARTeFACT 破损标注数据。

## 待补充

- 数据源的具体接口与许可
- 指标实现
- 运行环境
