#!/bin/bash
# Mem-Switch Docker Run Script
# 本地运行 Mem-Switch 后端

set -e

echo "🚀 Mem-Switch Docker Run"
echo "========================"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# 拉取最新镜像或构建
if docker image inspect mem-switch-backend:latest > /dev/null 2>&1; then
    echo "Using existing image..."
else
    echo "Pulling latest image..."
    docker pull mem-switch-backend:latest
fi

# 运行容器
docker run -d \
  --name mem-switch-backend \
  -p 8765:8765 \
  -v mem-switch-data:/root/.local/share/Mem-Switch \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  mem-switch-backend:latest

echo "✅ Mem-Switch backend is running at http://localhost:8765"