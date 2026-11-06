from __future__ import annotations

import argparse
import base64
import os
import posixpath
import stat
import sys
import time
from pathlib import Path

import paramiko


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


HOST = os.environ.get("M05_SSH_HOST", "connect.nmb2.seetacloud.com")
PORT = int(os.environ.get("M05_SSH_PORT", "25357"))
USERNAME = os.environ.get("M05_SSH_USER", "root")


def connect() -> paramiko.SSHClient:
    password = os.environ.get("M05_SSH_PASSWORD")
    if not password:
        raise RuntimeError("M05_SSH_PASSWORD is required")
    last_error: Exception | None = None
    for attempt in range(1, 6):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                HOST,
                port=PORT,
                username=USERNAME,
                password=password,
                timeout=20,
                banner_timeout=45,
                auth_timeout=30,
            )
            return client
        except Exception as exc:
            client.close()
            last_error = exc
            if attempt < 5:
                time.sleep(4 * attempt)
    raise RuntimeError("Unable to establish SSH connection after five attempts") from last_error


def ensure_remote_dir(sftp: paramiko.SFTPClient, path: str) -> None:
    current = "/"
    for part in path.strip("/").split("/"):
        if not part:
            continue
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def upload(local_path: Path, remote_path: str) -> None:
    client = connect()
    try:
        sftp = client.open_sftp()
        try:
            ensure_remote_dir(sftp, posixpath.dirname(remote_path))
            sftp.put(str(local_path), remote_path)
            print(f"uploaded {local_path.name} -> {remote_path}")
        finally:
            sftp.close()
    finally:
        client.close()


def _download_tree(sftp: paramiko.SFTPClient, remote: str, local: Path) -> None:
    info = sftp.stat(remote)
    if stat.S_ISDIR(info.st_mode):
        local.mkdir(parents=True, exist_ok=True)
        for entry in sftp.listdir_attr(remote):
            _download_tree(sftp, posixpath.join(remote, entry.filename), local / entry.filename)
        return
    local.parent.mkdir(parents=True, exist_ok=True)
    sftp.get(remote, str(local))


def download(remote_path: str, local_path: Path) -> None:
    client = connect()
    try:
        sftp = client.open_sftp()
        try:
            _download_tree(sftp, remote_path, local_path)
            print(f"downloaded {remote_path} -> {local_path}")
        finally:
            sftp.close()
    finally:
        client.close()


def run(command: str, timeout: int) -> None:
    client = connect()
    try:
        _, stdout, stderr = client.exec_command(command, timeout=timeout)
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(65536).decode("utf-8", errors="replace"), end="")
            if stderr.channel.recv_stderr_ready():
                print(
                    stderr.channel.recv_stderr(65536).decode("utf-8", errors="replace"),
                    end="",
                )
            time.sleep(0.05)
        while stdout.channel.recv_ready():
            print(stdout.channel.recv(65536).decode("utf-8", errors="replace"), end="")
        while stderr.channel.recv_stderr_ready():
            print(stderr.channel.recv_stderr(65536).decode("utf-8", errors="replace"), end="")
        status = stdout.channel.recv_exit_status()
        if status:
            raise RuntimeError(f"Remote command failed with exit status {status}")
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("command", nargs="?")
    run_parser.add_argument("--base64-command")
    run_parser.add_argument("--timeout", type=int, default=900)

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("local_path", type=Path)
    upload_parser.add_argument("remote_path")

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("remote_path")
    download_parser.add_argument("local_path", type=Path)

    args = parser.parse_args()
    if args.action == "run":
        command = args.command
        if args.base64_command:
            command = base64.b64decode(args.base64_command).decode("utf-8")
        if not command:
            raise RuntimeError("A command or --base64-command is required")
        run(command, args.timeout)
    elif args.action == "upload":
        upload(args.local_path, args.remote_path)
    else:
        download(args.remote_path, args.local_path)


if __name__ == "__main__":
    main()
