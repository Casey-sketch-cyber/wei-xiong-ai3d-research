from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np


def command_output(command: list[str]) -> str:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return "not installed"
    return (result.stdout or result.stderr).strip()


def main() -> None:
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    environment = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "cgroup_cpu_max": (
            Path("/sys/fs/cgroup/cpu.max").read_text(encoding="utf-8").strip()
            if Path("/sys/fs/cgroup/cpu.max").exists()
            else None
        ),
        "numpy": np.__version__,
        "gpu": command_output(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader",
            ]
        ),
        "cuda_compiler": command_output(["nvcc", "--version"]),
    }
    try:
        import scipy

        environment["scipy"] = scipy.__version__
    except ImportError:
        environment["scipy"] = None
    try:
        import matplotlib

        environment["matplotlib"] = matplotlib.__version__
    except ImportError:
        environment["matplotlib"] = None
    try:
        import torch

        environment.update(
            {
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "cudnn": torch.backends.cudnn.version(),
            }
        )
    except ImportError:
        environment["torch"] = None
    with (output / "environment.json").open("w", encoding="utf-8") as handle:
        json.dump(environment, handle, ensure_ascii=False, indent=2)
    freeze = command_output([sys.executable, "-m", "pip", "freeze"])
    (output / "pip_freeze.txt").write_text(freeze + "\n", encoding="utf-8")
    print(json.dumps(environment, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
