#!/bin/bash
# Mem-Switch Build Script
# 支持多平台构建

set -e

PLATFORM=$(uname -s)
ARCH=$(uname -m)

echo "Mem-Switch 构建脚本"
echo "==================="
echo "平台: $PLATFORM ($ARCH)"

# 检查依赖
check_deps() {
    if ! command -v npm &> /dev/null; then
        echo "错误: npm 未安装"
        exit 1
    fi

    if ! command -v cargo &> /dev/null; then
        echo "错误: Rust/Cargo 未安装"
        echo "安装: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        exit 1
    fi
}

# 前端构建
build_frontend() {
    echo ""
    echo "构建前端..."
    cd frontend
    npm install
    npm run build
    cd ..
    echo "前端构建完成"
}

# Tauri 构建
build_tauri() {
    echo ""
    echo "构建 Tauri 应用..."

    case "$PLATFORM" in
        Linux)
            if grep -qi "microsoft" /proc/version 2>/dev/null; then
                echo "检测到 WSL 环境"
                # 在 WSL 中可能需要 X Server 或 WSLg
                if [ -z "$WAYLAND_DISPLAY" ] && [ -z "$DISPLAY" ]; then
                    echo "警告: 未检测到图形环境，某些功能可能受限"
                fi
            fi
            cargo tauri build
            ;;
        Darwin)
            cargo tauri build
            ;;
        MINGW*|CYGWIN*|MSYS*)
            cargo tauri build
            ;;
        *)
            echo "错误: 不支持的平台"
            exit 1
            ;;
    esac

    echo "Tauri 构建完成"
}

# 显示用法
usage() {
    echo ""
    echo "用法: ./scripts/build.sh [命令]"
    echo ""
    echo "命令:"
    echo "  all          构建前端和 Tauri (默认)"
    echo "  frontend     仅构建前端"
    echo "  tauri        仅构建 Tauri"
    echo "  check        检查依赖"
    echo "  help         显示此帮助"
}

# 主逻辑
case "${1:-all}" in
    all)
        check_deps
        build_frontend
        build_tauri
        ;;
    frontend)
        build_frontend
        ;;
    tauri)
        build_tauri
        ;;
    check)
        check_deps
        echo "依赖检查通过"
        ;;
    help)
        usage
        ;;
    *)
        echo "未知命令: $1"
        usage
        exit 1
        ;;
esac

echo ""
echo "构建完成！"
