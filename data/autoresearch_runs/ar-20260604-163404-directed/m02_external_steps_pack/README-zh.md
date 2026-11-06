# M02 External Steps Pack

日期：2026-06-04

用途：把 M02 剩余的外部/人工步骤准备成可直接执行的材料。当前自动实验、人评包、图表和验证器已经完成；严格 M02 还需要 ArtEmis/WikiArt 授权数据和真人评分。

## 文件

- `artemis_access_request_template-zh.md`：ArtEmis 数据授权申请文本和填写要点。
- `artemis_access_live_check-zh.md`：2026-06-04 联网核验后的访问边界记录。
- `artemis_authorization_record_template-zh.md`：授权通过后的 Terms/authorization 留档模板。
- `human_evaluation_protocol-zh.md`：真人评价执行协议。
- `rater_invitation_template-zh.md`：邀请评价者的中文消息模板。
- `rater_consent_template-zh.md`：评价者参与说明与同意模板。
- `rater_metadata_template.csv`：匿名评价者背景信息记录表。
- `human_evaluation_ethics_checklist-zh.md`：伦理与审稿检查清单。
- `post_artemis_data_plan-zh.md`：拿到 ArtEmis/WikiArt 授权数据后的接入计划。
- `external_steps_status.json`：当前外部步骤状态。

## 官方来源

- ArtEmis 官网：`https://artemisdataset.org/`
- ArtEmis 代码仓库：`https://github.com/optas/artemis`

官网说明 ArtEmis 数据集约含 455K emotion attribution/explanation，覆盖约 80K WikiArt artworks；下载需要填写官方表单并接受 Terms of Use。代码仓库也要求先通过表单下载相关数据，再使用预处理脚本。

本包的 `artemis_access_live_check-zh.md` 已把上述联网核验结果和当前本地缺口固化为可审计记录。

## 当前状态

- ArtEmis/WikiArt 授权：pending human action。
- 真人评分：pending human evaluators。
- 自动实验包：pass。
- 人评材料包：pass。
- 一键验证：pass。

## 建议执行顺序

1. 使用 `artemis_access_request_template-zh.md` 填写 ArtEmis 官方表单。
2. 获得授权后，按 `post_artemis_data_plan-zh.md` 放置数据并建立正式 M02 ArtEmis 实验。
3. 同时招募至少 2 名评价者，发送 `rater_invitation_template-zh.md`。
4. 评价者按 `human_evaluation_protocol-zh.md` 完成 `m02_human_audit_pack\annotation_template.csv`。
5. 人评 CSV 回收后运行：

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack
python analyze_annotations.py annotation_rater01.csv annotation_rater02.csv
```
