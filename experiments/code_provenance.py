"""Identify the checkout and Python source bytes used for a model invocation."""

import hashlib
import os
import subprocess
from pathlib import Path


def _hash_parts(parts):
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(len(part)).encode("ascii"))
        digest.update(b"\0")
        digest.update(part)
    return digest.hexdigest()


def capture_code_provenance(source_dir=None):
    """Record Git metadata and a fingerprint of the local experiment modules."""
    source_dir = Path(source_dir or Path(__file__).parent).resolve()
    sources = sorted(
        path for path in source_dir.glob("*.py") if path.is_file() and not path.is_symlink()
    )
    source_parts = (
        part
        for path in sources
        for part in (path.name.encode("utf-8"), path.read_bytes())
    )
    snapshot = {
        "source_python_sha256": _hash_parts(source_parts),
        "source_python_count": len(sources),
        "git_head": None,
        "git_dirty": None,
        "git_diff_sha256": None,
    }
    checkout = source_dir.parent
    if not (checkout / ".git").exists():
        return {**snapshot, "git_state": "source_archive"}

    # Resolve the checkout from these modules, independent of the caller's cwd.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"

    def git(*args):
        return subprocess.run(
            ("git", "-C", str(checkout), *args),
            env=env, capture_output=True, check=True,
        ).stdout

    try:
        head = git("rev-parse", "HEAD").decode("ascii").strip()
    except FileNotFoundError:
        return {**snapshot, "git_state": "git_executable_missing"}
    status = git("status", "--porcelain=v1", "--untracked-files=normal", "-z")
    diff_args = ("diff", "--binary", "--no-color", "--no-ext-diff", "--no-textconv")
    staged = git(*diff_args, "--cached", "HEAD", "--")
    unstaged = git(*diff_args, "--")
    return {
        **snapshot,
        "git_state": "checkout",
        "git_head": head,
        "git_dirty": bool(status),
        "git_diff_sha256": _hash_parts((staged, unstaged)),
    }
