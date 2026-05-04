# Mem-Switch

跨平台桌面记忆管理应用 / Cross-platform desktop memory management app

[English Version](./README-en.md)

![Version](https://img.shields.io/badge/version-0.1.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue)

---

## ✨ 核心功能 / Features

### 记忆管理 / Memory Management
- **批量导入**：支持多文件同时导入，并发控制（2 文件/秒），自动去重
- **记忆提取**：从 AI 对话中自动提取偏好习惯、专业知识、项目上下文
- **记忆编辑**：支持修改内容、类型、维度
- **记忆合并**：AI 智能识别相似记忆并建议合并
- **记忆失效**：手动标记或自动过期（可配置）
- **使用统计**：追踪调用次数和最后调用时间

### 统一搜索中心 / Unified Search Center
- **多范围搜索**：同时搜索记忆库和知识库
- **智能算法**：小数据量 (<1000) 使用 LIKE 搜索，大数据量使用向量搜索
- **搜索结果缓存**：5 分钟 TTL，提升重复搜索性能
- **搜索历史**：记录最近搜索
- **热门搜索**：显示高频搜索内容

### 知识库管理 / Knowledge Base
- **文档导入**：支持 PDF/DOCX/TXT/MD
- **向量检索**：语义搜索相关文档片段
- **分块存储**：自动文档分块

### 对话导入 / Conversation Import
- **多平台支持**：Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes / JSON / Markdown / 剪贴板
- **向导式导入**：5 步流程（来源 → 文件 → 预览 → 导入 → 结果）
- **进度追踪**：实时显示成功/跳过/失败数量
- **失败处理**：部分保留策略，支持重试失败文件

### 通道路由 / Channel Routing
- **默认通道**：原始 AI 响应
- **记忆通道**：注入相关记忆的增强响应
- **独立配置**：为每个 AI 工具配置召回数量和相似度阈值

### 用户体验 / User Experience
- **首次引导**：5 步 Onboarding 向导（欢迎 → Ollama → 模型 → 导入 → 完成）
- **Toast 通知**：友好的成功/错误/警告提示
- **错误处理**：智能错误消息，支持操作撤销/重试
- **Cloud 风格 UI**：浅色主题，蓝色主色调，卡片式设计

### 系统特性 / System Features
- **硬件自适应**：自动检测硬件推荐合适模型
- **纯本地部署**：数据不上云，保护隐私
- **跨平台打包**：Windows (NSIS) / Linux (AppImage/deb) / macOS (DMG)

---

## 📦 安装 / Installation

### Windows
1. 下载 `Mem-Switch_x.x.x_x64-setup.exe`
2. 运行安装程序，**可自定义安装位置**
3. 完成安装，支持中文/英文界面

### macOS
```bash
# 下载并挂载 DMG
hdiutil attach Mem-Switch_x.x.x_x64.dmg
# 拖入 Applications 文件夹
```

### Linux

**AppImage (推荐 / Recommended)**:
```bash
chmod +x Mem-Switch_x.x.x_amd64.AppImage
./Mem-Switch_x.x.x_amd64.AppImage
```

**deb 包**:
```bash
sudo dpkg -i mem-switch_0.1.0_amd64.deb
```

**WSL/WSLg 用户 / Users**:
```bash
# 自动检测图形环境 / Auto-detect graphics environment
./linux-launch.sh
```

详细打包说明见 [PACKAGING.md](PACKAGING.md)

---

## 🚀 快速开始 / Quick Start

### 1. 首次启动 / First Launch
应用启动后显示 Onboarding 向导：
1. 欢迎界面 - 功能概览
2. Ollama 配置 - 连接测试
3. 模型选择 - 推荐并下载模型
4. 数据导入 - 可选现在导入或稍后
5. 完成 - 开始使用

### 2. 配置 Ollama
确保 Ollama 运行中：
```bash
ollama serve
```
应用会自动连接 `http://localhost:11434`，也支持自定义地址。

### 3. 对话导入 / Import Conversations
1. 点击侧边栏「对话导入」
2. 选择数据源平台（Claude Code / Codex / 等）
3. 拖拽或选择多个文件（可多选）
4. 预览确认，点击「开始导入」
5. 查看进度（成功/跳过/失败）

### 4. 查看和管理记忆 / Manage Memories
- 点击「记忆库」查看提取的记忆
- 点击记忆卡片可**编辑**、**失效**、**删除**
- 查看调用统计（调用次数、最后调用时间）
- 使用搜索框语义搜索记忆

### 5. 统一搜索 / Unified Search
1. 点击侧边栏顶部搜索按钮 🔍
2. 勾选搜索范围（记忆库 / 知识库）
3. 输入查询词，实时显示结果
4. 查看搜索历史和热门搜索

### 6. 知识库 / Knowledge Base
1. 创建知识库
2. 上传文档（支持多文件）
3. 使用搜索或统一搜索检索

### 7. 记忆通道路由 / Memory Channel Routing
为每个 AI 开发工具配置：
- 召回数量（默认 5 条）
- 相似度阈值（默认 0.7）
- 注入位置（system/user）

---

## 🛠️ 开发 / Development

### 环境要求 / Requirements
- Node.js >= 18
- Python >= 3.10
- Rust >= 1.70 (仅打包需要 / packaging only)

### 初始化 / Setup
```bash
# Windows (PowerShell)
.\scripts\setup-dev.ps1

# Linux/Mac
./scripts/setup-dev.sh
```

### 开发模式 / Development Mode

**方式 1: 浏览器预览 / Browser Preview**
```bash
# 终端 1: 启动后端 / Start backend
cd backend
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 终端 2: 启动前端 / Start frontend
cd frontend
npm install
npm run dev
```

**方式 2: 完整桌面应用 / Full Desktop App**
```bash
npm run tauri dev
```

### 打包 / Build

**Linux** (AppImage + deb):
```bash
./scripts/build-linux.sh
```
输出：`src-tauri/target/release/bundle/`

**Windows** (cargo-xwin 跨平台构建):
```bash
./scripts/build-windows-docker.sh
```
输出：`dist/windows/`

**macOS** (DMG):
```bash
cd src-tauri
cargo tauri build --target aarch64-apple-darwin
cargo tauri build --target x86_64-apple-darwin
```

详见 [PACKAGING.md](PACKAGING.md)

### Docker 部署 / Docker Deploy
```bash
docker-compose up -d
```
访问 http://localhost:5173

---

## 🏗️ 技术架构 / Architecture

```
┌──────────────────────────────────────┐
│      Tauri v2 桌面框架 (Rust)        │
│      - NSIS / AppImage / DMG         │
└─────────────────┬────────────────────┘
                  │ IPC
┌─────────────────▼────────────────────┐
│      前端 UI (Svelte 5 + Runes)      │
│  - 记忆库/知识库/导入/设置/搜索       │
│  - OnboardingWizard / Toast          │
└─────────────────┬────────────────────┘
                  │ HTTP API
┌─────────────────▼────────────────────┐
│      Python 后端 (FastAPI)           │
│  - SearchService (缓存 + 超时)        │
│  - MemoryService (编辑/合并/失效)    │
│  - BatchImportService (并发控制)      │
│  - KnowledgeService / ChannelManager │
└─────────────────┬────────────────────┘
                  │
┌─────────────────▼────────────────────┐
│      数据存储                         │
│  - Qdrant/Chroma (向量存储)          │
│  - SQLite (元数据/配置)              │
│  - Ollama (本地 LLM + Embedding)     │
└──────────────────────────────────────┘
```

---

## 📊 性能优化 / Performance

| 优化项 / Optimization | 策略 / Strategy |
|----------------------|-----------------|
| 搜索响应 / Search Response | 小数据量 LIKE < 1000 条，大数据量向量搜索 / LIKE < 1000 items, vector for large data |
| 搜索结果缓存 / Search Cache | 5 分钟 TTL，减少重复计算 / 5 min TTL, reduce repeated computation |
| 搜索超时控制 / Search Timeout | 30 秒超时，防止长时间等待 / 30 sec timeout, prevent long waits |
| 批量导入并发 / Batch Import | Semaphore(2) 限制并发数 / Concurrency limit |
| 导入去重 / Import Dedup | session_id 检查，跳过已导入 / session_id check, skip duplicates |
| Embedding 计算 / Embedding Calc | 循环外批量计算，减少调用次数 / Batch outside loop, reduce calls |

---

## 📁 数据存储 / Data Storage

- **向量数据**：Qdrant PersistentClient (本地文件 `~/.local/share/Mem-Switch/qdrant_storage`)
- **结构化数据**：SQLite (`~/.local/share/Mem-Switch/metadata.db`)
- **LLM**：Ollama (本地推理 + Embedding)
- **用户配置**：YAML (`~/.config/mem-switch/config.yaml`)

---

## 📝 更新日志 / Changelog

### v0.1.7 (2026-05-04)
- 修复 GitHub Actions workflow 在 Windows 上的 shell 语法错误
- 修复 publish job 缺少 checkout 步骤的问题

### v0.1.0 (2026-04-30)
- ✅ 批量导入与后台处理
- ✅ 记忆管理增强（编辑/合并/失效/统计）
- ✅ 统一搜索中心
- ✅ 首次使用引导（Onboarding）
- ✅ Toast 通知系统增强
- ✅ 错误处理优化
- ✅ 搜索性能优化（缓存 + 超时）
- ✅ 跨平台打包支持
- ✅ Cloud 风格 UI 升级

---

## 🤝 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！/ Issues and Pull Requests welcome!

## 📄 License

MIT