# 本地核对与复现入口

## 仓库完整性

在仓库根目录运行：

    python tools/check_handoff.py

该命令使用 Python 标准库，检查来源清单、源文件哈希、Python 语法、数据/凭据排除、当前作者信息与 M03 主检验边界。它不运行 GPU、下载数据或重算全部确认实验。

## 轻量环境

建议 Python 3.12；按需安装 requirements-review.txt。该文件为审稿与图表工具入口，不是 GPU 实验的锁定环境。原环境版本见 provenance 和 M05 的 05_audit/environment_remote/。

## LaTeX

进入 manuscripts/m03_jcde/01_manuscript/latex/：

    pdflatex -interaction=nonstopmode -halt-on-error main.tex
    biber main
    pdflatex -interaction=nonstopmode -halt-on-error main.tex
    pdflatex -interaction=nonstopmode -halt-on-error main.tex

需要 MiKTeX 或 TeX Live 中的 pdflatex、biber、biblatex-apa 等包。若使用 latexmk，需要其 Perl 运行时。本机历史上 pdflatex/biber 可编译，latexmk 曾因没有 Perl 启动失败。

生成后的 PDF 和受影响页应做视觉检查。正文仍使用现有 journal template conventions；此仓库整理不重写论文内容。

## M03 表格与图表

当前数值分析输出在 experiments/m03_q2_confirmatory_20260715/results_final/artifacts_20260729/analysis/。可先复制输出目录到新的工作位置，用 make_confirmatory_figures.py 的 --analysis-root 和 --output-root 重画统计图。

Figure 1 的可编辑 PPTX 在 manuscripts/m03_jcde/02_figures_tables/publication_figures/fig1_framework_confirmatory_4model_editable.pptx。其历史 .mjs 脚本依赖原机器的 D: 路径和 @oai/artifact-tool；其他电脑可以直接用 PowerPoint 编辑 PPTX，或先改为可用的工具和相对路径再运行。

Figure 3 代表性网格图需要远程 mesh、GPU/nvdiffrast 和渲染依赖。本地有已导出的图，不能据此宣称已完成网格图的独立重渲染。

原 make_submission_materials.py 依据 manuscripts/m03_jcde/ 的固定结构工作。编辑正文后应同步作者栏、checklist、cover letter、PDF 和源文件包；检查 ORCID 的投稿系统要求。

Git 中的投稿目录采用展开保存方式。重复的源文件 ZIP、实验补充 ZIP 与大型 TIFF 已排除；需要实际提交时，从本仓库源文件重建这些打包文件，并按最新期刊要求检查上传顺序。

## M05 小规模代码检查

不需原始数据的单元检查：

    python -m unittest discover -s data/autoresearch_runs/ar-20260903-m05-visrepair3d/03_pilot -p test_core.py
    python -m unittest discover -s data/autoresearch_runs/ar-20260903-m05-visrepair3d/04_full_experiment -p test_formal.py

完整 480-case 结果的几何重放需要未上传的完整 case/layout 记录。仓库中保留 full_results.csv、统计汇总、图表、冻结配置和审查记录；这些能帮助分析已有数字，不替代逐病例审计。

## 已知需要迁移的路径

- 一些发现实验和投稿构建脚本仍引用 D:/AutoResearch。
- 一些远程推理与统计 shell 脚本固定使用 /root/autodl-tmp。
- 旧人评工具引用仓库外图片；现阶段仅作历史工具参考。
- 旧 AutoResearch 全流程工具和数据库未纳入，此仓库保留与三条研究有关的独立脚本和材料。

先按任务检查 --help 和读参数默认值，再改路径或运行。不要直接把旧 inventory/验证脚本中缺失原始数据的报错解释成原实验无效。
