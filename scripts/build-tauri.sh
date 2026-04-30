#!/bin/bash
set -e

echo "=== Mem-Switch Linux Build ==="

# 检查 Rust
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust not installed. Install from https://rustup.rs"
    exit 1
fi

echo "Rust version: $(rustc --version)"

# 构建前端
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# 安装 Rust 依赖
echo "Installing Rust dependencies..."
cd src-tauri
cargo fetch
cd ..

# 构建 Tauri
echo "Building Tauri (this may take a while)..."
npm run tauri build -- --bundles deb,appimage

echo ""
echo "=== Build complete ==="
echo "Output in src-tauri/target/release/bundle/"
ls -la src-tauri/target/release/bundle/ 2>/dev/null || echo "No bundle directory found"
