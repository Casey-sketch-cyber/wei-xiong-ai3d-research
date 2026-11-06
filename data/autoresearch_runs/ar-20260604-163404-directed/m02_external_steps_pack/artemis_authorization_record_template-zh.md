# ArtEmis/WikiArt 授权留档模板

日期：2026-06-05

用途：获得 ArtEmis/WikiArt 数据访问权限后，记录授权和使用边界。请不要把受限原始数据公开发布。

## 授权状态

- 申请日期：
- 授权/通过日期：
- 申请邮箱或账号：
- 官方表单/邮件记录保存位置：
- Terms of Use 文件或截图保存位置：
- 是否允许论文中展示原图：
- 是否允许内部共享：
- 是否允许公开派生指标：

## 数据放置

本地建议目录：

```text
D:\AutoResearch\data\restricted\artemis\
```

远程建议目录：

```text
/root/autodl-tmp/m03/restricted/artemis/
```

建议文件：

- `authorization_record.md`：本留档填写后的版本；
- `terms_of_use.*`：官方 Terms of Use 或截图；
- `download_notes.md`：下载日期、来源、文件列表、校验信息；
- `annotations/`：ArtEmis 标注文件；
- `wikiart_refs/`：WikiArt 图像路径、引用或访问说明。

## 使用边界

- 只用于本研究的非商业学术评估；
- 不公开再分发 ArtEmis 原始标注；
- 不公开再分发 WikiArt 原图，除非官方条款允许；
- 论文和补充材料只放聚合指标、匿名统计、必要的合法示例；
- 若官方条款与本模板冲突，以官方条款为准。

## 后续命令

授权数据放置完成后，在 run 根目录运行：

```powershell
python check_external_steps.py
python run_m02_strict_followup.py
```

