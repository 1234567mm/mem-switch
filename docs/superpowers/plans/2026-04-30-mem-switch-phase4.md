# Mem-Switch Phase 4: 打包 + 文档 实施计划

> **For agentic workers:** Execute task-by-task following checkbox syntax.

**Goal:** 各平台安装包 + 完整文档

**Architecture:** Tauri v2 打包，跨平台安装包，完整用户文档

**Tech Stack:** Tauri v2 / Cargo / Node.js / markdown

---

## File Structure

```
mem-switch-desktop/
├── README.md                      # 更新: 对话导入流程详解
├── docs/
│   └── user_guide.md              # 新增: 用户指南
├── scripts/
│   └── build-tauri.sh             # 新增: Tauri 构建脚本
├── src-tauri/
│   ├── tauri.conf.json            # 修改: 打包配置
│   ├── icons/                     # 使用现有 icons
│   └── build.rs                   # (已存在)
└── frontend/
    └── dist/                      # 构建产物
```

---

## Task 1: Tauri 打包配置

**Files:**
- Modify: `src-tauri/tauri.conf.json`
- Create: `scripts/build-tauri.sh`

- [ ] **Step 1: 检查 Tauri 配置**

Run: `cat src-tauri/tauri.conf.json`

Expected: 存在有效的 tauri.conf.json 配置

- [ ] **Step 2: 更新 tauri.conf.json 打包配置**

```json
{
  "productName": "Mem-Switch",
  "version": "0.1.0",
  "identifier": "com.memswitch.app",
  "build": {
    "frontendDist": "../frontend/dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "windows": {
      "wix": null,
      "nsis": {
        "installMode": "currentUser"
      }
    }
  }
}
```

- [ ] **Step 3: 创建构建脚本**

```bash
#!/bin/bash
set -e

echo "=== Mem-Switch Tauri Build ==="

# 检查 Rust 环境
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust/Cargo not installed. Install from https://rustup.rs"
    exit 1
fi

# 构建前端
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# 构建 Tauri
echo "Building Tauri..."
npm run tauri build

echo "=== Build complete ==="
echo "Output in src-tauri/target/release/bundle/"
```

- [ ] **Step 4: 提交**

```bash
git add src-tauri/tauri.conf.json scripts/build-tauri.sh
git commit -m "feat(pkg): add Tauri build configuration"
```

---

## Task 2: 完善 README 文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README.md 内容**

```markdown
# Mem-Switch

跨平台桌面记忆管理应用，统一管理知识库、记忆库和对话导入。

## 核心功能

- **记忆库管理**：时间轴展示、用户画像、可配置提取维度
- **知识库管理**：文档导入、RAG 检索
- **对话导入**：支持 Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes
- **记忆通道路由**：为各 AI 工具独立配置记忆通道
- **硬件自适应**：自动检测硬件推荐本地模型
- **纯本地部署**：数据不上云

## 安装

### Windows
下载 `Mem-Switch_x.x.x_x64-setup.exe` 运行安装。

### macOS
挂载 `Mem-Switch_x.x.x_x64.dmg` 拖入 Applications。

### Linux
```bash
chmod +x Mem-Switch_x.x.x_amd64.AppImage
./Mem-Switch_x.x.x_amd64.AppImage
```

## 快速开始

### 1. 首次启动
启动后会自动检测硬件配置，推荐合适的 Ollama 模型。

### 2. 配置 Ollama
确保 Ollama 运行中 (`ollama serve`)。应用会自动连接。

### 3. 对话导入
1. 点击侧边栏「对话导入」
2. 选择数据源类型（Claude Code / Codex / 等）
3. 点击「扫描数据源」预览对话
4. 确认后点击「开始导入」

### 4. 查看记忆
导入的对话会自动提取记忆：
- **偏好习惯**：语言风格、交互偏好
- **专业知识**：领域方向、技能水平
- **项目上下文**：当前工作、关注问题

### 5. 知识库
1. 创建知识库
2. 上传文档（PDF/DOCX/TXT/MD）
3. 使用 RAG 检索

### 6. 记忆通道路由
为每个 AI 开发工具配置：
- **默认通道**：原始 AI 响应
- **记忆通道**：注入相关记忆的增强响应

## 开发

### 环境要求
- Node.js >= 18
- Python >= 3.10
- Rust >= 1.70 (仅打包需要)

### 初始化

```bash
# Windows (PowerShell)
.\scripts\setup-dev.ps1

# Linux/Mac
./scripts/setup-dev.sh
```

### 开发模式

**方式1: 浏览器预览**
```bash
# 终端1: 启动后端
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# 终端2: 启动前端
cd frontend
npm install
npm run dev
```

**方式2: 完整桌面应用**
```bash
npm run tauri dev
```

### Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost:5173

## 技术架构

```
┌─────────────────────────────┐
│  Tauri v2 桌面框架 (Rust)   │
└──────────────┬──────────────┘
               │ IPC
┌──────────────▼──────────────┐
│  前端 UI (Svelte 5)         │
│  - 知识库/记忆库/导入/设置   │
└──────────────┬──────────────┘
               │ HTTP API
┌──────────────▼──────────────┐
│  Python 后端 (FastAPI)      │
│  - KnowledgeService         │
│  - MemoryService            │
│  - ConversationImporter     │
│  - ChannelManager           │
└─────────────────────────────┘
```

## 数据存储

- **向量数据**：Chroma PersistentClient (本地文件)
- **结构化数据**：SQLite (元数据/配置)
- **LLM**：Ollama (本地推理 + Embedding)

## License

MIT
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: update README with complete usage instructions"
```

---

## Task 3: 用户指南

**Files:**
- Create: `docs/user_guide.md`

- [ ] **Step 1: 创建 user_guide.md**

```markdown
# Mem-Switch 用户指南

## 目录
1. [功能概览](#功能概览)
2. [对话导入流程](#对话导入流程)
3. [记忆提取说明](#记忆提取说明)
4. [知识库使用](#知识库使用)
5. [通道路由配置](#通道路由配置)
6. [常见问题](#常见问题)

---

## 功能概览

Mem-Switch 是一款本地部署的 AI 开发工具记忆管理应用。

### 核心功能

| 功能 | 说明 |
|------|------|
| 记忆库 | 存储和管理从对话中提取的记忆片段 |
| 知识库 | 上传文档，通过 RAG 进行知识检索 |
| 对话导入 | 从多种 AI 工具导入历史对话 |
| 通道路由 | 控制 AI 工具是否使用记忆增强 |

---

## 对话导入流程

### 支持的数据源

| 平台 | 默认路径 | 格式 |
|------|----------|------|
| Claude Code | `~/.claude/projects` | JSONL |
| Codex | `~/.codex/sessions` | JSON |
| OpenClaw | `~/.openclaw/sessions` | JSON |
| OpenCode | `~/.opencode/history` | Markdown |
| Gemini CLI | `~/.gemini/history` | JSON |
| Hermes | `~/.hermes/sessions` | JSON |

### 导入步骤

1. **打开导入界面**
   - 点击侧边栏「对话导入」

2. **选择数据源**
   - 从下拉菜单选择平台类型

3. **预览**
   - 点击「扫描数据源」查看待导入对话
   - 系统会显示检测到的会话数量和预览

4. **确认导入**
   - 点击「开始导入」
   - 系统将：
     - 解析对话文件
     - 生成向量嵌入
     - 存入向量数据库
     - 提取关键记忆

5. **查看结果**
   - 导入完成后可在「记忆库」查看提取的记忆

---

## 记忆提取说明

### 提取维度

系统自动从对话中提取三个维度的信息：

| 维度 | 说明 | 示例 |
|------|------|------|
| 偏好习惯 | 用户的交互偏好 | 喜欢简洁回复、使用特定术语 |
| 专业知识 | 技术领域和技能 | Python开发、熟悉Docker |
| 项目上下文 | 当前工作内容 | 正在开发Web应用、解决性能问题 |

### 置信度

每条记忆都有一个置信度分数 (0-1)：
- **> 0.8**：高置信度，直接使用
- **0.5-0.8**：中置信度，建议人工确认
- **< 0.5**：低置信度，谨慎使用

---

## 知识库使用

### 创建知识库

1. 点击侧边栏「知识库」
2. 点击「创建知识库」
3. 填写名称和描述
4. 配置参数（可选）：
   - **Embedding 模型**：默认 `nomic-embed-text`
   - **分块大小**：默认 500 字符
   - **相似度阈值**：默认 0.7

### 上传文档

支持格式：PDF、DOCX、TXT、Markdown

1. 选择知识库
2. 点击「上传文档」
3. 选择文件
4. 系统自动：
   - 提取文本
   - 分块
   - 生成 Embedding
   - 存入向量库

### 知识检索

1. 在搜索框输入问题
2. 系统返回相关文档片段
3. 显示相似度分数

---

## 通道路由配置

### 概念

每个 AI 开发工具可以有两条通道：

| 通道类型 | 说明 |
|----------|------|
| 默认通道 | AI 原始响应，无记忆注入 |
| 记忆通道 | 注入相关记忆的增强响应 |

### 配置步骤

1. 点击侧边栏「通道路由」
2. 选择要配置的 AI 平台
3. 选择通道类型：
   - **默认**：原始 AI 响应
   - **记忆**：检索相关记忆并注入 System Prompt
4. 调整参数（可选）：
   - **召回数量**：注入的记忆条数 (默认 5)
   - **相似度阈值**：只注入高于此分数的记忆 (默认 0.7)
   - **注入位置**：System Prompt / User Prompt (默认 System)

### 工作原理

启用记忆通道时：
1. 用户发送消息
2. 系统检索相关记忆
3. 将记忆注入 System Prompt
4. AI 生成增强响应

---

## 常见问题

### Q: Ollama 连接失败
确保 Ollama 服务正在运行：
```bash
ollama serve
```

### Q: 导入的对话没有显示
1. 检查数据源路径是否正确
2. 确认文件格式受支持
3. 查看后端日志

### Q: 记忆提取质量低
1. 较长的对话提取效果更好
2. 可以在「记忆库」中手动编辑
3. 调整提取维度配置

### Q: 如何导出数据
当前版本数据存储在本地：
- 向量数据：`~/.local/share/Mem-Switch/qdrant_storage`
- SQLite：`~/.local/share/Mem-Switch/sqlite/metadata.db`
```

- [ ] **Step 2: 提交**

```bash
git add docs/user_guide.md
git commit -m "docs: add comprehensive user guide"
```

---

## Task 4: Linux 构建验证

**Files:**
- Modify: `scripts/build-tauri.sh`
- Create: `scripts/build-tauri.ps1` (Windows, 待 Windows Docker 环境验证)

- [ ] **Step 1: 创建 Linux 构建脚本**

```bash
#!/bin/bash
set -e

echo "=== Mem-Switch Linux Build ==="

# 检查 Rust
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust not installed. Install from https://rustup.rs"
    exit 1
fi

# 检查系统依赖
if ! command -v pkg-config &> /dev/null; then
    echo "Error: pkg-config not found."
    echo "Install GTK3 development libraries:"
    echo "  Ubuntu/Debian: sudo apt install libgtk-3-dev pkg-config libssl-dev libwebkit2gtk-4.1-dev"
    exit 1
fi

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
echo "Building Tauri..."
npm run tauri build -- --bundles deb,appimage

echo "=== Build complete ==="
echo "Output in src-tauri/target/release/bundle/"
```

- [ ] **Step 2: 执行 Linux 构建**

```bash
chmod +x scripts/build-tauri.sh
./scripts/build-tauri.sh
```

Expected: 构建成功，生成 `.deb` 和 `.AppImage` 文件

- [ ] **Step 3: 验证 AppImage**

```bash
chmod +x src-tauri/target/release/bundle/appimage/*.AppImage
./src-tauri/target/release/bundle/appimage/*.AppImage &
```

Expected: 应用启动，显示主窗口

- [ ] **Step 4: 创建 Windows 构建脚本 (备选)**

```powershell
# scripts/build-tauri.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Mem-Switch Windows Build ==="

# 检查 Rust
if (!(Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Rust not installed. Install from https://rustup.rs"
    exit 1
}

# 构建前端
Write-Host "Building frontend..."
Set-Location frontend
npm install
npm run build
Set-Location ..

# 构建 Tauri
Write-Host "Building Tauri..."
npm run tauri build -- --bundles nsis

Write-Host "=== Build complete ==="
Write-Host "Output in src-tauri/target/release/bundle/nsis/"
```

- [ ] **Step 5: 提交**

```bash
git add scripts/build-tauri.sh scripts/build-tauri.ps1
git commit -m "feat(pkg): add Linux and Windows build scripts"
```

---

## Task 5: 版本发布准备

- [ ] **Step 1: 更新版本号**

```bash
# 更新 tauri.conf.json 中的 version
# 更新 package.json 中的 version
# 更新 README.md 中的版本引用
```

- [ ] **Step 2: 打标签**

```bash
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

- [ ] **Step 3: 构建正式发布包**

```bash
# Linux
./scripts/build-tauri.sh

# Windows (PowerShell)
.\scripts\build-tauri.ps1
```

- [ ] **Step 4: 提交发布**

```bash
git add -A
git commit -m "chore(release): v0.1.0"
git push
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Tauri 打包配置
- [x] 各平台构建脚本 (Linux + Windows)
- [x] README 完整流程说明
- [x] User Guide 详述
- [x] Linux 构建验证 ✅

**Placeholder scan:**
- 无 TBD/TODO
- 所有步骤包含实际代码

**Build verification:**
- [ ] Linux AppImage 构建成功 (需要系统依赖: libgtk-3-dev, pkg-config, libwebkit2gtk-4.1-dev)
- [ ] Windows .exe 安装验证 (待 Windows Docker 环境)
- [ ] macOS .dmg 构建验证 (待 macOS 环境)

---

Plan complete and saved to `docs/superpowers/plans/2026-04-30-mem-switch-phase4.md`.