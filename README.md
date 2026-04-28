# Mem-Switch

跨平台桌面记忆管理应用，统一管理知识库、记忆库和对话导入。

## 核心功能

- 记忆库管理：时间轴展示、用户画像、可配置提取维度
- 知识库管理：文档导入、RAG检索
- 对话导入：支持 Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes
- 记忆通道路由：为各AI工具独立配置记忆通道
- 硬件自适应：自动检测硬件推荐本地模型
- 纯本地部署：数据不上云

## 开发状态

- Phase 1: 基础框架搭建 (进行中)
- Phase 2: 核心服务开发 (待开始)
- Phase 3: 记忆代理 + UI完善 (待开始)
- Phase 4: 打包 + 文档 (待开始)

## 开发

```bash
# 初始化开发环境
./scripts/setup-dev.sh

# 启动开发模式
npm run dev
```

## 技术栈

- 桌面框架: Tauri v2 (Rust)
- 前端: Svelte 5 + TailwindCSS 4
- 后端: Python FastAPI
- 向量存储: Qdrant (本地)
- 本地LLM: Ollama
- 元数据: SQLite