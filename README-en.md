# Mem-Switch

Cross-platform desktop memory management app. Unified management of knowledge base, memory store, and conversation imports.

![Version](https://img.shields.io/badge/version-0.1.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue)

## ✨ Features

### Memory Management
- **Batch Import**: Multi-file import with concurrency control (2 files/sec), auto-dedup
- **Memory Extraction**: Auto-extract preferences, knowledge, project context from AI conversations
- **Memory Editing**: Edit content, type, dimensions
- **Memory Merge**: AI identifies similar memories and suggests merging
- **Memory Expiry**: Manual or auto-expiry (configurable)
- **Usage Stats**: Track call count and last call time

### Unified Search Center
- **Multi-scope Search**: Search both memory and knowledge bases
- **Smart Algorithm**: LIKE search for small data (<1000), vector search for large data
- **Search Cache**: 5 min TTL for repeated queries
- **Search History**: Recent searches
- **Trending Searches**: Popular search terms

### Knowledge Base
- **Document Import**: PDF/DOCX/TXT/MD support
- **Vector Retrieval**: Semantic document fragment search
- **Chunked Storage**: Auto document chunking

### Conversation Import
- **Multi-platform Support**: Claude Code / Codex / OpenClaw / OpenCode / Gemini CLI / Hermes / JSON / Markdown / Clipboard
- **Wizard Flow**: 5 steps (source → file → preview → import → result)
- **Progress Tracking**: Real-time success/skip/fail counts
- **Partial Failure**: Preserve partial results, retry failed files

### Channel Routing
- **Default Channel**: Original AI response
- **Memory Channel**: Enhanced response with relevant memories injected
- **Per-tool Config**: Recall count and similarity threshold per AI tool

### User Experience
- **Onboarding Wizard**: 5-step guide (welcome → Ollama → model → import → done)
- **Toast Notifications**: Success/error/warning toasts
- **Error Handling**: Smart error messages, undo/retry
- **Cloud-style UI**: Light theme, blue accent, card design

### System Features
- **Hardware Adaptive**: Auto-detect hardware, recommend suitable models
- **Local-only**: Data stays local, privacy protected
- **Cross-platform**: Windows (NSIS) / Linux (AppImage/deb) / macOS (DMG)

## 📦 Installation

### Windows
1. Download `Mem-Switch_x.x.x_x64-setup.exe`
2. Run installer, **customizable install path**
3. Done, supports Chinese/English UI

### macOS
```bash
# Download and mount DMG
hdiutil attach Mem-Switch_x.x.x_x64.dmg
# Drag to Applications
```

### Linux

**AppImage (Recommended)**:
```bash
chmod +x Mem-Switch_x.x.x_amd64.AppImage
./Mem-Switch_x.x.x_amd64.AppImage
```

**deb package**:
```bash
sudo dpkg -i mem-switch_0.1.0_amd64.deb
```

**WSL/WSLg Users**:
```bash
# Auto-detect graphics environment
./linux-launch.sh
```

See [PACKAGING.md](PACKAGING.md) for detailed packaging instructions.

## 🚀 Quick Start

### 1. First Launch
Onboarding wizard on first launch:
1. Welcome - Feature overview
2. Ollama Config - Connection test
3. Model Select - Recommended and download
4. Import - Optional now or later
5. Done - Start using

### 2. Configure Ollama
Ensure Ollama is running:
```bash
ollama serve
```
App auto-connects to `http://localhost:11434`, custom address supported.

### 3. Import Conversations
1. Click "Import" in sidebar
2. Select platform (Claude Code / Codex / etc.)
3. Drag or select multiple files
4. Preview, click "Start Import"
5. View progress (success/skip/fail)

### 4. Manage Memories
- Click "Memory" to view extracted memories
- Click memory card to **edit**, **expire**, **delete**
- View stats (call count, last call time)
- Semantic search via search box

### 5. Unified Search
1. Click search button 🔍 in sidebar
2. Check scope (Memory / Knowledge)
3. Enter query, see results live
4. View search history and trending

### 6. Knowledge Base
1. Create knowledge base
2. Upload documents (multi-file supported)
3. Search via dedicated or unified search

### 7. Memory Channel Routing
Configure per AI tool:
- Recall count (default 5)
- Similarity threshold (default 0.7)
- Injection position (system/user)

## 🛠️ Development

### Requirements
- Node.js >= 18
- Python >= 3.10
- Rust >= 1.70 (packaging only)

### Setup
```bash
# Windows (PowerShell)
.\scripts\setup-dev.ps1

# Linux/Mac
./scripts/setup-dev.sh
```

### Development Mode

**Option 1: Browser Preview**
```bash
# Terminal 1: Start backend
cd backend
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev
```

**Option 2: Full Desktop App**
```bash
npm run tauri dev
```

### Build

**Linux** (AppImage + deb):
```bash
./scripts/build-linux.sh
```
Output: `src-tauri/target/release/bundle/`

**Windows** (cargo-xwin cross-build):
```bash
./scripts/build-windows-docker.sh
```
Output: `dist/windows/`

**macOS** (DMG):
```bash
cd src-tauri
cargo tauri build --target aarch64-apple-darwin
cargo tauri build --target x86_64-apple-darwin
```

See [PACKAGING.md](PACKAGING.md) for details.

### Docker Deploy
```bash
docker-compose up -d
```
Access http://localhost:5173

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│      Tauri v2 Desktop (Rust)         │
│      - NSIS / AppImage / DMG         │
└─────────────────┬────────────────────┘
                  │ IPC
┌─────────────────▼────────────────────┐
│      Frontend UI (Svelte 5 + Runes)  │
│  - Memory/Knowledge/Import/Settings   │
│  - OnboardingWizard / Toast          │
└─────────────────┬────────────────────┘
                  │ HTTP API
┌─────────────────▼────────────────────┐
│      Python Backend (FastAPI)        │
│  - SearchService (cache + timeout)   │
│  - MemoryService (edit/merge/expiry)  │
│  - BatchImportService (concurrency)  │
│  - KnowledgeService / ChannelManager │
└─────────────────┬────────────────────┘
                  │
┌─────────────────▼────────────────────┐
│      Data Storage                    │
│  - Qdrant/Chroma (vector)           │
│  - SQLite (metadata/config)         │
│  - Ollama (local LLM + Embedding)   │
└──────────────────────────────────────┘
```

## 📊 Performance

| Optimization | Strategy |
|-------------|----------|
| Search Response | LIKE < 1000 items, vector for large data |
| Search Cache | 5 min TTL, reduce repeated computation |
| Search Timeout | 30 sec timeout, prevent long waits |
| Batch Import | Semaphore(2) concurrency limit |
| Import Dedup | session_id check, skip duplicates |
| Embedding Calc | Batch outside loop, reduce calls |

## 📁 Data Storage

- **Vector Data**: Qdrant PersistentClient (local `~/.local/share/Mem-Switch/qdrant_storage`)
- **Structured Data**: SQLite (`~/.local/share/Mem-Switch/metadata.db`)
- **LLM**: Ollama (local inference + Embedding)
- **User Config**: YAML (`~/.config/mem-switch/config.yaml`)

## 📝 Changelog

### v0.1.7 (2026-05-04)
- Fixed GitHub Actions workflow shell syntax error on Windows runners
- Fixed publish job missing checkout step

### v0.1.0 (2026-04-30)
- ✅ Batch import with background processing
- ✅ Memory management (edit/merge/expiry/stats)
- ✅ Unified search center
- ✅ Onboarding wizard
- ✅ Toast notification system
- ✅ Error handling optimization
- ✅ Search performance (cache + timeout)
- ✅ Cross-platform packaging
- ✅ Cloud-style UI upgrade

## 🤝 Contributing

Issues and Pull Requests welcome!

## 📄 License

MIT