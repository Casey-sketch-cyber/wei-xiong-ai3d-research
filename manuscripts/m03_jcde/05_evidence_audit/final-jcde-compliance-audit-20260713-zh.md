# M03 JCDE 终审记录

审查日期：2026-07-13

## 1. 当前稿件

- 题目：*Style-induced volumetric contraction in TripoSR: A controlled benchmark of stylised input transformations*
- 目标期刊：*Journal of Computational Design and Engineering*
- 正文 PDF：22 页，A4
- 摘要：204 个英文单词
- 参考文献：38 条
- 正式图：4 张
- 正式表：3 张
- 作者、单位、邮箱和通讯作者信息已写入正文及投稿清单。
- 正文中未保留单独的 “ORCID iDs” 段落。

## 2. 本轮实质性修改

1. 将核心结论收敛为 TripoSR 在本基准上的“风格诱发体积收缩”，避免把单模型结果泛化为所有 image-to-3D 模型。
2. 明确 100 个 Objaverse 对象、1 个 photo 条件和 5 个受控艺术化条件，共 600 次重建的配对实验结构。
3. 明确绝对真值体积未被用作主指标，因为 100 个真值网格中只有 1 个满足 watertight 条件；体积比由同一对象的 stylised/photo 两个 watertight TripoSR 输出计算。
4. 增加 photo-baseline quality 分层分析。所有风格在较强 photo 基线组中仍表现出体积收缩，但聚合 F-score 增益主要集中在较弱 photo 基线对象；photo F-score 最高四分位中，五种风格的平均 F-score 变化均为负。
5. 保留 marching-cubes resolution 128 的 30-object 稳健性复跑，用来检验体积收缩是否由主实验 resolution 64 的网格提取设置偶然造成。
6. 重写摘要、引言、方法、结果、讨论、局限性和结论，使“稳定的体积结果”和“受基线质量调节的表面指标结果”分开陈述。
7. Figure 1 已改为真实实验样本，并提供可编辑 PPTX；Figures 2--4 已统一标题、注释和结论措辞。

## 3. 数值复核

Photo F-score@0.05 的中位数为 0.236823。按该中位数分层后，高质量 photo 组中的平均 stylised/photo 体积比分别为：edge 0.365、flat colour 0.707、low detail 0.329、sketch 0.393、watercolour 0.427，均仍低于 1。最高 photo-quality 四分位中的平均 F-score 变化分别为 -0.049、-0.018、-0.060、-0.040 和 -0.014。

主实验的平均体积比分别为：edge 0.332、flat colour 0.500、low detail 0.305、sketch 0.257、watercolour 0.343。相应的配对检验、置信区间、每对象结果和 128-resolution 稳健性数据均已放入复现包。

## 4. 技术与版式检查

- 主项目 LaTeX 已完整执行 PDFLaTeX、Biber 和重复 PDFLaTeX 编译，正文为 22 页。
- 最终 LaTeX 源码 ZIP 已在独立目录解压并重新编译；输出同为 22 页，日志无未解析引用、排版溢出、LaTeX 错误或包警告。
- 正文 PDF 与投稿目录中的 Main Document PDF 的 SHA-256 完全一致。
- Figure 1 的可编辑 PPTX 已完成溢出和版式检查；四张正式图均已在正文渲染页中检查，无文字重叠、截断或面板错位。
- Highlights、Alt Text 和 10 页投稿清单均已渲染检查；通讯作者姓名、单位、邮箱和 ORCID 已填入期刊清单。
- 投稿 ZIP 完整性测试通过，共 5 个规定文件。
- 复现 ZIP 完整性测试通过，共 69 个文件，不包含自身、缓存目录或损坏条目。
- 复现包中的分层分析和 Figure 2--4 生成脚本已实际运行验证。

## 5. 投稿前仍需作者确认

以下信息无法从实验记录中可靠推断，因此未代填或编造：

1. 四位作者的 CRediT author contributions。
2. Funding / acknowledgements；若确实无资助，也需要作者明确确认后写入 “No specific funding” 类声明。
3. APC-paying author 及其账单地址。
4. 公开代码与数据仓库的 DOI 或稳定链接；如投稿前尚未存档，可按期刊流程在最终版本补充。

除上述作者控制信息外，当前稿件和文件包已完成本轮计划中的内容、证据、格式、编译、图表和复现检查。
