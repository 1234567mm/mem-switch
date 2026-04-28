# Mem-Switch

跨平台桌面记忆管理应用，统一管理知识库、记忆库和对话导入。

## 核心功能

- 记忆库管理：时间轴展示、用户画像、可配置提取维度
- 知识库管理：文档导入、RAG检索
- 对话导入：支持 Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes
- 记忆通道路由：为各AI工具独立配置记忆通道
- 硬件自适应：自动检测硬件推荐本地模型
- 纯本地部署：数据不上云

## 开发

### 初始化

```bash
# Windows (PowerShell)
.\scripts\setup-dev.ps1

# Linux/Mac/WSL
./scripts/setup-dev.sh
```

### 启动开发模式

**方式1: 浏览器预览 (无需Tauri)**
```bash
# 终端1: 启动后端
conda activate mem-switch
cd backend
uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# 终端2: 启动前端
cd frontend
npm run dev

# 浏览器打开 http://localhost:5173
```

**方式2: 完整桌面应用**
```bash
# 终端1: 启动后端
conda activate mem-switch
cd backend
uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# 终端2: 启动Tauri
npm run tauri dev
```

## 技术栈

- 桌面框架: Tauri v2 (Rust)
- 前端: Svelte 5 + TailwindCSS 4
- 后端: Python FastAPI
- 向量存储: Qdrant (本地)
- 本地LLM: Ollama
- 元数据: SQLite