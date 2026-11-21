# 推理代码的版本记录

启动模型前，`run_pilot.py` 从脚本所在目录获取 Git 和源码摘要，`run_followup.py` 与 `run_latent_aligned.py` 共用此入口。优先使用服务器数据盘上的 Git 检出目录。每次推理前确认该目录处于预定提交，数据及输出路径单独指向数据盘。

```bash
git -C "$CODE" rev-parse HEAD
git -C "$CODE" status --porcelain=v1
```

| `code_provenance` 字段 | 来源 |
| --- | --- |
| `git_head` | `git rev-parse HEAD` |
| `git_dirty` | Git porcelain 状态中是否出现索引、工作树或未忽略的未跟踪条目 |
| `git_diff_sha256` | 暂存区相对 HEAD、工作树相对暂存区的两段二进制 diff，分别在原始字节前加十进制长度和 NUL，再按顺序计算 SHA-256 |
| `source_python_sha256` | `experiments/` 下按文件名排序的顶层普通 Python 文件，包括其中的未跟踪文件。每个 UTF-8 文件名与原始内容分别使用相同的长度前缀 |
| `git_state` | Git 检出目录为 `checkout`，无 `.git` 的源码副本为 `source_archive`，检测不到 Git 可执行文件为 `git_executable_missing` |

差异摘要采用 `git diff --binary --no-color --no-ext-diff --no-textconv --cached HEAD --` 和 `git diff --binary --no-color --no-ext-diff --no-textconv --`。记录只保留摘要、状态与 Python 文件数。旧源码副本无可核验 Git 提交时，对应三个 Git 字段为 `null`，仍可核对实际 Python 文件的摘要。

每次调用先将记录写到 `provenance/<model>/<execution_id>.json`。`run_<model>.json` 汇总总计数并记录最近完成调用的身份。新评分用 `execution_id` 关联自己的运行记录，续跑可追踪不同批次。技术烟雾测试的 `smoke_<model>.json` 也包含 `code_provenance`。旧评分的版本证据以原有存档为准。

## 克利夫兰未扩张扩散组

以原尺度主实验的冻结目录为参考，分别用主实验的 SDXL 和 PowerPaint 环境执行。该组仍采用相同种子和模型配置。输入洞使用原计分掩码，PowerPaint 保留安全检查。收到安全拦截时，旧的失败记录和主比较的可用率口径继续适用。

```bash
"$PYTHON" -B "$CODE/experiments/run_latent_aligned.py" prepare \
  --arm native-main-unexpanded-diffusion --reference "$CMA_ROOT/prepared" --run-dir "$UNEXPANDED"
"$PYTHON" -B "$CODE/experiments/run_latent_aligned.py" run \
  --arm native-main-unexpanded-diffusion --model sdxl --models-dir "$MODELS" --run-dir "$UNEXPANDED"
"$POWERPAINT_PYTHON" -B "$CODE/experiments/run_latent_aligned.py" run \
  --arm native-main-unexpanded-diffusion --model powerpaint --models-dir "$MODELS" --run-dir "$UNEXPANDED"
"$PYTHON" -B "$CODE/experiments/diagnostic_metrics.py" \
  --run-dir "$UNEXPANDED" --output "$SCORES"
```

PowerPaint 存在未输出的条件时，推理入口返回状态码 2。查阅 `failures/` 核对逐个失败原因。诊断分数与推理输出使用不同文件路径。
