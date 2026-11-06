# 文件选择与排除

上传内容来自：

- manuscripts/m03_jcde：当前论文、期刊模板、脚本、图表、最新作者投稿文件、写作分析与审核资料。
- experiments/m03_q2_confirmatory_20260715：确认实验代码、协议、任务索引、统计结果和论文图。
- experiments/m03_hunyuan21_pilot_20260714 与 experiments/m03_metric_validity_pilot_20260714：先导实验、方法演变和旧结果摘要。
- data/autoresearch_runs/ar-20260604-163404-directed：M02/M03 早期扫描、独立脚本、汇总与审查说明。
- data/autoresearch_runs/ar-20260903-m05-visrepair3d：M05 方法、检索、代码、正式数值结果与审查。
- external/humanizer、external/AI-Research-SKILLs 的 ml-paper-writing、external/nature-skills 的技能与参考文件。

为便于 Claude 在已有目录基础上继续工作，保留原相对路径。数据目录名不表示原始数据被上传。

明确排除完整原始数据、mesh、权重、完整生成布局与逐病例重放记录、缓存、环境、C: 内部状态、SSH/API 凭据、未审核聊天记录、浏览器带令牌下载链接、重复 ZIP、超大 TIFF、临时 QA 图片和无关研究项目。

从 2 GB 以上相关工作目录中筛选出约 72 MiB 的代码/文档/图表/数字摘要。文件数、字节和来源哈希以 SOURCE_MANIFEST.json 及后续 VALIDATION.json 的实际记录为准。

导入文件保持原字节与换行，以保留冻结协议和数值结果的 SHA-256；新交接说明使用 UTF-8。若扫描发现硬编码凭据，应仅在导出的副本中改成环境配置；原工作区不修改。REDACTION_REPORT.json 只记录文件和次数，不记录被清除的值。

没有给第三方内容新增许可。技能的原许可证已保留，期刊模板仅供本研究按期刊要求写作与提交时参考使用。
