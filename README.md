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

或安装 .deb 包：
```bash
sudo dpkg -i Mem-Switch_0.1.0_amd64.deb
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
