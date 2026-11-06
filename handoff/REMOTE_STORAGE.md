# 远程数据与环境

本次 GitHub 整理没有连接服务器，以下位置来自现有代码和历史清单。服务器实例、端口、容量和数据存在性需要在实际重跑前核对。SSH 密码与 API key 未放入仓库。

## 历史项目根目录

| 内容 | 已记录的远程路径 | 本地对应代码 |
| --- | --- | --- |
| M03 四模型确认实验 | /root/autodl-tmp/m03_q2_confirmatory_20260715 | experiments/m03_q2_confirmatory_20260715 |
| M03 发现实验与 M02 | /root/autodl-tmp/m03 | data/autoresearch_runs/ar-20260604-163404-directed |
| M02 EmoArt-100 输入 | /root/autodl-tmp/m03/datasets/emoart5k_m02_sample100 | 同上 remote_scripts |
| M02 TripoSR 输出与评估 | /root/autodl-tmp/m03/outputs/m02_emoart100 | 同上 remote_scripts |
| M05 | 由 M05 remote_ops.py 与实验配置核对实际根目录 | data/autoresearch_runs/ar-20260903-m05-visrepair3d |

M03 四模型根目录的 dataset、inputs、inference、evaluation 和 render_diagnostics 等实际内容均以远程文件为准。当前只保留对象索引、执行计划、数值汇总、环境/来源摘要和论文图片。

## 连接配置

复制根目录 .env.example 为本机 .env 并自行填入有效连接信息。现有脚本大多读取环境变量，不会自动载入 .env；运行前需要由终端或本机密钥管理器导出相应变量。

- M03 remote_ops.py：M03_SSH_HOST、M03_SSH_PORT、M03_SSH_USER、M03_SSH_PASSWORD。
- M05 remote_ops.py：M05_SSH_HOST、M05_SSH_PORT、M05_SSH_USER、M05_SSH_PASSWORD。
- 早期 inventory 脚本：REMOTE_HOST、REMOTE_PORT、REMOTE_USER、REMOTE_PW。

历史脚本默认的 host/port 仅是旧配置，不能保证对应仍在运行的实例。不要将密码、私钥、代理凭据或 API key 写回脚本/文档/提交记录。

## 需要保留在远程的内容

- Google Scanned Objects 和 EmoArt 等完整数据；
- 原始三维对象、修复后的 ground truth 和完整艺术化输入；
- 四模型生成的完整三维文件、纹理与原始渲染；
- 模型权重、Hugging Face 缓存、conda/venv；
- M05 完整生成布局、full_cases.json、completed.jsonl 等逐病例记录。

仓库中保留的数字结果表是已有实验的核对依据；重建完整生成数据仍需要相应远程资源。

## 学术资源加速

AutoDL 终端中可运行：

    source /etc/network_turbo

Hugging Face 镜像可设置 HF_ENDPOINT=https://hf-mirror.com，缓存放数据盘。GitHub 下载遇阻可先查看 https://ghproxy.link/ 的当时文档。若代理影响其他网络，按实际环境取消 http_proxy、https_proxy 等变量。

加速是否可用需要当时验证。硬件、CUDA、Python 与具体三维模型依赖以历史 provenance 和远程环境记录为起点，不默认所有环境互通。
