#!/usr/bin/env python3
"""
Mem-Switch Sidecar Preparation Script
将 PyInstaller 打包的 backend 二进制文件复制到 Tauri sidecar 目录
"""
import shutil
import os
import platform

system = platform.system().lower()
machine = platform.machine().lower()
target = os.environ.get("TAURI_SIDECAR_TARGET")

if target:
    ext = ".exe" if system == "windows" else ""
else:
    arch_map = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}
    arch = arch_map.get(machine, machine)
    if system == "windows":
        target, ext = f"{arch}-pc-windows-msvc", ".exe"
    elif system == "darwin":
        target, ext = f"{arch}-apple-darwin", ""
    elif system == "linux":
        target, ext = f"{arch}-unknown-linux-gnu", ""
    else:
        raise RuntimeError(f"Unsupported: {system}")

source = f"backend/dist/mem-switch-backend{ext}"
dest_dir = "src-tauri/binaries"
dest = f"{dest_dir}/mem-switch-backend-{target}{ext}"
os.makedirs(dest_dir, exist_ok=True)

if os.path.exists(source):
    shutil.copy2(source, dest)
    print(f"[OK] {source} -> {dest}")
else:
    raise FileNotFoundError(source)
