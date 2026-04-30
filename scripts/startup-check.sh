#!/bin/bash
# Mem-Switch Startup Check Script
# 检测图形环境并在无桌面环境下提供提示

set -e

echo "Mem-Switch 启动检查..."
echo "========================"

# 检查是否在 WSL 环境中
if grep -qi "microsoft" /proc/version 2>/dev/null; then
    echo "检测到 WSL 环境"
    IS_WSL=true
else
    IS_WSL=false
fi

# 检查图形环境
check_display() {
    if [ -n "$WAYLAND_DISPLAY" ]; then
        echo "检测到 Wayland 显示: $WAYLAND_DISPLAY"
        return 0
    elif [ -n "$DISPLAY" ]; then
        echo "检测到 X11 显示: $DISPLAY"
        return 0
    else
        return 1
    fi
}

# 检查 WSLg (Windows 11 + WSL2)
check_wslg() {
    if [ -f /usr/lib/wslg/wslg-helper ]; then
        echo "检测到 WSLg 支持"
        return 0
    fi
    return 1
}

# 主检查逻辑
if check_display; then
    echo "图形环境就绪"
    exit 0
elif check_wslg; then
    echo "WSLg 已启用，图形环境就绪"
    exit 0
elif [ "$IS_WSL" = true ]; then
    echo ""
    echo "错误: 未检测到图形环境"
    echo ""
    echo "在 WSL 中运行 Mem-Switch 需要以下之一:"
    echo ""
    echo "方案 1: 使用 WSLg (推荐 - Windows 11 + WSL2)"
    echo "  确保已安装 Windows 11 并升级到最新 WSL"
    echo "  运行: wsl --update"
    echo ""
    echo "方案 2: 使用 X Server"
    echo "  安装并启动 VcXsrv 或 X410"
    echo "  设置环境变量: export DISPLAY=localhost:0"
    echo ""
    echo "方案 3: 使用 Windows 子系统设置"
    echo "  安装 WSLg: wsl --install -d ubuntu"
    echo ""
    exit 1
else
    echo "错误: 未检测到图形环境"
    echo "请确保已安装桌面环境并设置了 DISPLAY 或 WAYLAND_DISPLAY"
    exit 1
fi
