#!/bin/bash
set -e

echo "=== Mem-Switch 开发环境初始化 ==="

# 检查系统依赖
echo "检查 Node.js..."
command -v node >/dev/null 2>&1 || { echo "错误: 需要 Node.js (>=18)"; exit 1; }
node_version=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$node_version" -lt 18 ]; then echo "错误: Node.js >= 18 required"; exit 1; fi

echo "检查 Python..."
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || { echo "错误: 需要 Python (>=3.10)"; exit 1; }

echo "检查 Conda..."
command -v conda >/dev/null 2>&1 || { echo "错误: 需要 Miniconda/Anaconda"; exit 1; }

echo "检查 Rust..."
command -v cargo >/dev/null 2>&1 || { echo "警告: Rust 未安装，请安装 https://rustup.rs"; }

echo "检查 Ollama..."
command -v ollama >/dev/null 2>&1 || echo "警告: Ollama 未安装，请安装 https://ollama.com"

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
cd ..

# 创建后端 conda 环境
echo "创建后端 conda 环境 (mem-switch)..."
conda create -n mem-switch python=3.10 -y 2>/dev/null || conda activate mem-switch
conda activate mem-switch
pip install -r backend/requirements.txt
conda deactivate

echo ""
echo "=== 初始化完成 ==="
echo ""
echo "启动开发模式:"
echo ""
echo "方式1 - 使用脚本 (需要conda):"
echo '  conda activate mem-switch'
echo '  cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload'
echo "  (新终端) npm run tauri dev"
echo ""
echo "方式2 - 分步启动:"
echo '  # 终端1: 启动后端'
echo '  conda activate mem-switch'
echo '  cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload'
echo ""
echo '  # 终端2: 启动前端'
echo '  cd frontend && npm run dev'
echo ""
echo '  # 终端3: 启动Tauri桌面应用'
echo '  npm run tauri dev'
echo ""
echo "方式3 - 仅启动后端和前端 (无桌面窗口):"
echo '  conda activate mem-switch'
echo '  cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload'
echo "  (新终端) cd frontend && npm run dev"
echo "  然后浏览器打开 http://localhost:5173"