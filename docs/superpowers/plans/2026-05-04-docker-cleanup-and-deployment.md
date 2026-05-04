# Docker 部署与清理计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理废弃文件，保留并增强 Docker 部署支持

**Architecture:** 保留 `Dockerfile.backend` 用于后端容器化部署，清理废弃的交叉编译文件

**Tech Stack:** Docker, Docker Compose, Python, Tauri

---

## 第一部分：清理废弃文件

### Task 1: 删除废弃的交叉编译脚本和文件

**Files:**
- Delete: `scripts/build-windows-docker.sh`
- Delete: `scripts/build.sh`
- Delete: `Dockerfile.windows-build`

- [ ] **Step 1: 删除废弃文件**

```bash
rm scripts/build-windows-docker.sh
rm scripts/build.sh
rm Dockerfile.windows-build
```

- [ ] **Step 2: 验证删除**

```bash
ls scripts/
# 应该只剩: build-linux.sh, build-tauri.sh, release.sh, setup-dev.ps1, setup-dev.sh, startup-check.sh
```

- [ ] **Step 3: 提交更改**

```bash
git add -A
git commit -m "cleanup: remove obsolete cross-compilation scripts

- scripts/build-windows-docker.sh (replaced by GitHub Actions native builds)
- scripts/build.sh (replaced by GitHub Actions native builds)
- Dockerfile.windows-build (replaced by GitHub Actions native builds)"
```

---

## 第二部分：清理构建缓存

### Task 2: 清理 src-tauri/target 构建缓存

**Files:**
- Delete: `src-tauri/target/` (所有构建产物)

- [ ] **Step 1: 清理构建缓存**

```bash
rm -rf src-tauri/target/
```

- [ ] **Step 2: 验证**

```bash
ls src-tauri/target/ 2>/dev/null || echo "target directory cleaned"
```

- [ ] **Step 3: 提交 (git 会自动忽略空的 target 目录)**

```bash
git add -A
git commit -m "cleanup: remove Tauri build cache"
```

---

## 第三部分：增强 Docker 部署支持

### Task 3: 更新 Dockerfile.backend 支持 ARM64 和 x86_64 多架构

**Files:**
- Modify: `Dockerfile.backend`

- [ ] **Step 1: 更新 Dockerfile.backend 支持多架构构建**

```dockerfile
# Mem-Switch Backend Docker Image
# 支持 x86_64 和 ARM64 架构

FROM --platform=$TARGETARCH python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-dev \
    librsvg2-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chromadb (not in requirements but needed)
RUN pip install --no-cache-dir chromadb

# Copy backend code
COPY backend/ .

# Create app data directory
RUN mkdir -p /root/.local/share/Mem-Switch

EXPOSE 8765

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765"]
```

- [ ] **Step 2: 更新 docker-compose.yml 支持多架构**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      platform: linux/amd64,linux/arm64
    ports:
      - "8765:8765"
    volumes:
      - mem-switch-data:/root/.local/share/Mem-Switch
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
      - QDRANT_HOST=qdrant:6334

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage

  frontend:
    image: node:20-slim
    working_dir: /app
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    command: sh -c "npm install && npm run dev -- --host"
    environment:
      - VITE_API_URL=http://localhost:8765

volumes:
  mem-switch-data:
  qdrant-data:
```

- [ ] **Step 3: 提交更改**

```bash
git add Dockerfile.backend docker-compose.yml
git commit -m "feat: enhance Docker deployment with multi-arch support and Qdrant vector DB"
```

---

## 第四部分：创建 Docker 打包脚本

### Task 4: 创建便捷的 Docker 构建和运行脚本

**Files:**
- Create: `scripts/docker-build.sh` - Docker 多架构构建脚本
- Create: `scripts/docker-run.sh` - Docker 本地运行脚本

- [ ] **Step 1: 创建 scripts/docker-build.sh**

```bash
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
```

- [ ] **Step 2: 创建 scripts/docker-run.sh**

```bash
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
```

- [ ] **Step 3: 设置执行权限**

```bash
chmod +x scripts/docker-build.sh scripts/docker-run.sh
```

- [ ] **Step 4: 提交**

```bash
git add scripts/docker-build.sh scripts/docker-run.sh
git commit -m "feat: add Docker build and run scripts"
```

---

## 验证清单

- [ ] `scripts/build-windows-docker.sh` 已删除
- [ ] `scripts/build.sh` 已删除
- [ ] `Dockerfile.windows-build` 已删除
- [ ] `src-tauri/target/` 已清理
- [ ] `Dockerfile.backend` 已更新支持多架构
- [ ] `docker-compose.yml` 已更新包含 Qdrant 服务
- [ ] `scripts/docker-build.sh` 已创建
- [ ] `scripts/docker-run.sh` 已创建
- [ ] 所有更改已提交

---

## 最终文件结构

```
Date_LIB/
├── Dockerfile.backend          # ✅ 保留，后端容器化部署
├── docker-compose.yml          # ✅ 保留，增强版
├── scripts/
│   ├── docker-build.sh         # ✅ 新增，Docker 构建脚本
│   ├── docker-run.sh           # ✅ 新增，Docker 运行脚本
│   ├── build-linux.sh          # ✅ 保留，本地参考
│   ├── build-tauri.sh          # ✅ 保留
│   ├── release.sh              # ✅ 保留
│   └── ...
├── src-tauri/target/           # 🗑️ 已清理
└── ...
```

---

## 回滚计划（如果需要）

```bash
# 回滚清理操作
git revert HEAD~1  # 回滚最后一次提交
```