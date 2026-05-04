#!/bin/bash
# Mem-Switch Docker Build Script
# 构建多架构 Docker 镜像

set -e

echo "🔨 Mem-Switch Docker Build"
echo "==========================="

# 构建多架构镜像
docker buildx build --platform linux/amd64,linux/arm64 \
  -t mem-switch-backend:latest \
  -t mem-switch-backend:$(date +%Y%m%d) \
  --push .

echo "✅ Docker image built and pushed"