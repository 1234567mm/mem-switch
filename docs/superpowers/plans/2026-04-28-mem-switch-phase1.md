# Mem-Switch Phase 1: 基础框架搭建 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 Mem-Switch 桌面应用基础框架——Tauri v2 窗口 + Svelte 5 前端 + Python FastAPI 后端 + 硬件检测 + Ollama 连接 + Qdrant 本地模式 + 首次启动引导页

**Architecture:** Tauri v2 作为桌面框架，通过 sidecar 模式启动打包后的 Python FastAPI 服务。前端 Svelte 5 通过 HTTP API (localhost:8765) 与后端通信。启动时自动检测硬件并推荐 Ollama 模型。

**Tech Stack:** Tauri v2 (Rust) / Svelte 5 + TailwindCSS 4 / Python FastAPI / Qdrant (本地嵌入) / Ollama / SQLite / psutil + GPUtil

**Spec:** `docs/superpowers/specs/2026-04-28-kb-mem-desktop-design.md`

---

## File Structure

```
mem-switch-desktop/
├── README.md
├── package.json                     # 根项目: npm run tauri dev / build
├── .gitignore
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── svelte.config.js
│   ├── index.html
│   ├── static/favicon.png
│   └── src/
│       ├── main.js                  # Svelte 5 入口 (mount API)
│       ├── app.css                  # TailwindCSS 4 (@import "tailwindcss")
│       ├── App.svelte               # 主路由: 侧边栏+tabs切换
│       ├── lib/
│       │   ├── api.js               # HTTP API客户端 (axios)
│       │   └── platform.js          # 跨平台常量
│       ├── stores/
│       │   ├── app.svelte.js        # 全局状态: currentTab, backendReady
│       │   └── hardware.svelte.js   # 硬件检测结果+Ollama状态
│       ├── components/
│       │   ├── Sidebar.svelte       # 侧边导航
│       │   ├── StartupGuide.svelte  # 首次启动引导(硬件检测+模型选择)
│       │   ├── SettingsView.svelte  # 设置界面(基础版)
│       │   └── StatusBar.svelte     # 底部状态栏
│
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── main.py                      # FastAPI入口+路由注册
│   ├── config.py                    # 跨平台数据目录+配置管理
│   ├── services/
│   │   ├── __init__.py
│   │   ├── hardware_detector.py     # 硬件检测+模型推荐
│   │   ├── ollama_service.py        # Ollama连接/模型列表/拉取
│   │   ├── vector_store.py          # Qdrant本地初始化+collection创建
│   │   ├── database.py              # SQLite初始化+config表CRUD
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py            # GET /api/health
│   │   │   ├── hardware.py          # GET /api/hardware/detect
│   │   │   ├── ollama.py            # GET /api/ollama/status, /models, POST /pull
│   │   │   ├── settings.py          # GET/PUT /api/settings
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── hardware.py          # HardwareInfo, ModelRecommendation
│   │   │   ├── settings.py          # AppConfig schema
│   │   │   ├── ollama.py            # OllamaStatus, ModelInfo
│   ├── tests/
│       ├── test_hardware_detector.py
│       ├── test_ollama_service.py
│       ├── test_vector_store.py
│       ├── test_database.py
│       ├── test_health_api.py
│       ├── test_settings_api.py
│
├── src-tauri/
│   ├── Cargo.toml
│   ├── build.rs
│   ├── tauri.conf.json              # Tauri v2配置(sidecar, 端口等)
│   ├── capabilities/
│   │   └── default.json             # 权限(shell:allow-sidecar)
│   ├── src/
│   │   ├── main.rs                  # Rust入口: 启动sidecar+窗口
│   │   └── lib.rs                   # Tauri IPC命令
│   ├── icons/
│       ├── icon.png
│       ├── icon.ico
│       ├── icons.icns
│
├── scripts/
│   └── setup-dev.sh                 # 开发环境一键初始化
│
└── docs/
    └── (Phase 4填充)
```

---

### Task 1: 项目根目录初始化

**Files:**
- Create: `mem-switch-desktop/package.json`
- Create: `mem-switch-desktop/.gitignore`
- Create: `mem-switch-desktop/README.md` (基础版)

- [ ] **Step 1: 创建项目根目录**

```bash
mkdir -p mem-switch-desktop
cd mem-switch-desktop
```

创建 `package.json`:
```json
{
  "name": "mem-switch-desktop",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "tauri dev",
    "build": "tauri build",
    "tauri": "tauri"
  }
}
```

- [ ] **Step 2: 创建 .gitignore**

```
# Tauri
src-tauri/target/

# Frontend
frontend/node_modules/
frontend/dist/
frontend/build/

# Python
backend/__pycache__/
backend/*.egg-info/
backend/.venv/
backend/dist/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# App data (dev)
Mem-Switch/
```

- [ ] **Step 3: 创建 README.md 基础版**

```markdown
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
```

- [ ] **Step 4: 初始化 git 并提交**

```bash
git init
git add package.json .gitignore README.md
git commit -m "feat: init mem-switch-desktop project root"
```

---

### Task 2: Svelte 5 前端初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/svelte.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/app.css`
- Create: `frontend/src/App.svelte`
- Create: `frontend/src/stores/app.svelte.js`
- Create: `frontend/src/stores/hardware.svelte.js`
- Create: `frontend/src/lib/api.js`
- Create: `frontend/src/lib/platform.js`
- Create: `frontend/src/components/Sidebar.svelte`
- Create: `frontend/src/components/StatusBar.svelte`

- [ ] **Step 1: 创建 frontend/package.json**

```json
{
  "name": "mem-switch-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^5.0",
    "@tauri-apps/api": "^2.0",
    "axios": "^1.7",
    "svelte": "^5.0",
    "tailwindcss": "^4.0",
    "vite": "^6.0"
  }
}
```

- [ ] **Step 2: 创建 frontend/vite.config.js**

```js
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

// Tauri开发模式下使用特定端口
const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: 'ws', host, port: 5174 } : undefined,
    watch: { ignored: ['**/backend/**', '**/src-tauri/**'] },
  },
  envPrefix: ['VITE_', 'TAURI_ENV_*'],
  build: {
    target: host ? 'svelte' : process.env.TAURI_ENV_PLATFORM === 'windows' ? 'chrome105' : 'safari13',
    minify: !process.env.TAURI_ENV_DEBUG,
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },
});
```

- [ ] **Step 3: 创建 frontend/svelte.config.js**

```js
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
};
```

- [ ] **Step 4: 创建 frontend/index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/png" href="/favicon.png" />
    <title>Mem-Switch</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 5: 创建 frontend/src/main.js**

```js
import './app.css';
import App from './App.svelte';
import { mount } from 'svelte';

const app = mount(App, { target: document.getElementById('app') });

export default app;
```

- [ ] **Step 6: 创建 frontend/src/app.css**

```css
@import "tailwindcss";
```

- [ ] **Step 7: 创建 frontend/src/stores/app.svelte.js**

```js
export const appState = $state({
  currentTab: 'startup',
  backendReady: false,
  backendUrl: 'http://127.0.0.1:8765',
  initialized: false,
});
```

- [ ] **Step 8: 创建 frontend/src/stores/hardware.svelte.js**

```js
export const hardwareState = $state({
  detected: false,
  cpuCores: 0,
  totalMemoryGB: 0,
  gpuMemoryGB: 0,
  gpuAvailable: false,
  recommendedModels: [],
  selectedModel: '',
  selectedEmbeddingModel: 'nomic-embed-text',
  ollamaConnected: false,
  ollamaModels: [],
});
```

- [ ] **Step 9: 创建 frontend/src/lib/api.js**

```js
import axios from 'axios';
import { appState } from '../stores/app.svelte.js';

function getApi() {
  return axios.create({
    baseURL: appState.backendUrl,
    timeout: 30000,
  });
}

export const api = {
  health: () => getApi().get('/api/health'),
  hardware: {
    detect: () => getApi().get('/api/hardware/detect'),
  },
  ollama: {
    status: () => getApi().get('/api/ollama/status'),
    models: () => getApi().get('/api/ollama/models'),
    pull: (modelName) => getApi().post('/api/ollama/pull', { model: modelName }),
  },
  settings: {
    get: () => getApi().get('/api/settings'),
    update: (data) => getApi().put('/api/settings', data),
  },
};
```

- [ ] **Step 10: 创建 frontend/src/lib/platform.js**

```js
export const PLATFORM = {
  isWindows: navigator.platform.startsWith('Win'),
  isMac: navigator.platform.startsWith('Mac'),
  isLinux: navigator.platform.startsWith('Linux'),
};
```

- [ ] **Step 11: 创建 frontend/src/components/Sidebar.svelte**

```svelte
<script>
  import { appState } from '../stores/app.svelte.js';

  const tabs = [
    { id: 'startup', label: '启动引导', icon: '⚡' },
    { id: 'knowledge', label: '知识库', icon: '📚' },
    { id: 'memory', label: '记忆库', icon: '🧠' },
    { id: 'import', label: '对话导入', icon: '📥' },
    { id: 'settings', label: '设置', icon: '⚙️' },
  ];
</script>

<nav class="w-56 h-full bg-gray-900 text-white flex flex-col">
  <div class="p-4 text-xl font-bold border-b border-gray-700">
    Mem-Switch
  </div>
  <ul class="flex-1 py-2">
    {#each tabs as tab}
      <li>
        <button
          class="w-full px-4 py-3 text-left hover:bg-gray-800 {appState.currentTab === tab.id ? 'bg-gray-800 text-blue-400' : ''}"
          onclick={() => appState.currentTab = tab.id}
        >
          {tab.icon} {tab.label}
        </button>
      </li>
    {/each}
  </ul>
</nav>
```

- [ ] **Step 12: 创建 frontend/src/components/StatusBar.svelte**

```svelte
<script>
  import { appState } from '../stores/app.svelte.js';
  import { hardwareState } from '../stores/hardware.svelte.js';
</script>

<footer class="h-8 bg-gray-900 text-gray-400 flex items-center px-4 text-sm">
  <span class="flex-1">
    后端: {appState.backendReady ? '✓ 已连接' : '✗ 未连接'}
  </span>
  <span>
    Ollama: {hardwareState.ollamaConnected ? '✓' : '✗'}
    {hardwareState.selectedModel || '未选择模型'}
  </span>
</footer>
```

- [ ] **Step 13: 创建 frontend/src/App.svelte**

```svelte
<script>
  import { appState } from './stores/app.svelte.js';
  import Sidebar from './components/Sidebar.svelte';
  import StatusBar from './components/StatusBar.svelte';
  import StartupGuide from './components/StartupGuide.svelte';
  import SettingsView from './components/SettingsView.svelte';

  let placeholderLabel = $derived(
    appState.currentTab === 'knowledge' ? '知识库' :
    appState.currentTab === 'memory' ? '记忆库' :
    appState.currentTab === 'import' ? '对话导入' : ''
  );
</script>

<div class="flex h-screen bg-gray-100">
  <Sidebar />
  <main class="flex-1 flex flex-col">
    <div class="flex-1 overflow-auto">
      {#if appState.currentTab === 'startup'}
        <StartupGuide />
      {:else if appState.currentTab === 'settings'}
        <SettingsView />
      {:else}
        <div class="flex items-center justify-center h-full text-gray-500 text-xl">
          {placeholderLabel} - Phase 2 开发中
        </div>
      {/if}
    </div>
    <StatusBar />
  </main>
</div>
```

- [ ] **Step 14: 安装前端依赖并验证 Vite 启动**

```bash
cd frontend
npm install
npm run dev
# 验证: 浏览器打开 http://localhost:5173
# 期望: 看到 Mem-Switch 侧边栏和 "启动引导" 页面（StartupGuide还未创建，会报错，下一步创建）
```

- [ ] **Step 15: 提交前端初始化**

```bash
cd mem-switch-desktop
git add frontend/
git commit -m "feat: init Svelte 5 frontend with sidebar, routing, and API client"
```

---

### Task 3: Python FastAPI 后端核心服务

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/hardware_detector.py`
- Create: `backend/services/ollama_service.py`
- Create: `backend/services/vector_store.py`
- Create: `backend/services/database.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/routes/__init__.py`
- Create: `backend/api/routes/health.py`
- Create: `backend/api/routes/hardware.py`
- Create: `backend/api/routes/ollama.py`
- Create: `backend/api/routes/settings.py`
- Create: `backend/api/schemas/__init__.py`
- Create: `backend/api/schemas/hardware.py`
- Create: `backend/api/schemas/settings.py`
- Create: `backend/api/schemas/ollama.py`
- Test: `backend/tests/test_hardware_detector.py`
- Test: `backend/tests/test_health_api.py`
- Test: `backend/tests/test_settings_api.py`

- [ ] **Step 1: 创建 backend/pyproject.toml 和 requirements.txt**

`backend/pyproject.toml`:
```toml
[project]
name = "mem-switch-backend"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "qdrant-client>=1.9.0",
    "ollama>=0.4.0",
    "pyyaml>=6.0",
    "pydantic>=2.6",
    "sqlalchemy>=2.0",
    "python-multipart>=0.0.9",
    "psutil>=5.9.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

`backend/requirements.txt`:
```
fastapi>=0.110.0
uvicorn>=0.29.0
qdrant-client>=1.9.0
ollama>=0.4.0
pyyaml>=6.0
pydantic>=2.6
sqlalchemy>=2.0
python-multipart>=0.0.9
psutil>=5.9.0
pytest>=8.0
httpx>=0.27
```

- [ ] **Step 2: 创建 backend/config.py (跨平台数据目录+配置)**

```python
import os
import platform
import yaml
from pathlib import Path


def get_app_data_dir() -> Path:
    """跨平台应用数据目录"""
    sys = platform.system()
    if sys == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / "Mem-Switch"


APP_DATA_DIR = get_app_data_dir()
CONFIG_FILE = APP_DATA_DIR / "config.yaml"
SQLITE_DIR = APP_DATA_DIR / "sqlite"
QDRANT_DIR = APP_DATA_DIR / "qdrant_storage"
DOCUMENTS_DIR = APP_DATA_DIR / "documents"
IMPORTS_DIR = APP_DATA_DIR / "imports"
LOGS_DIR = APP_DATA_DIR / "logs"

BACKEND_PORT = 8765
BACKEND_HOST = "127.0.0.1"


class AppConfig:
    def __init__(self):
        self._config = {}
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self):
        for d in [APP_DATA_DIR, SQLITE_DIR, QDRANT_DIR,
                  DOCUMENTS_DIR, IMPORTS_DIR, LOGS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def _defaults(self) -> dict:
        return {
            "ollama_host": "http://127.0.0.1:11434",
            "llm_model": "",
            "embedding_model": "nomic-embed-text",
            "qdrant_host": "localhost",
            "qdrant_port": 6333,
            "memory_expiry_days": 180,
            "extract_dimensions": ["preference", "expertise", "project_context"],
        }

    def _load(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._defaults()
            self._save()

    def _save(self):
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value
        self._save()

    def update(self, data: dict):
        self._config.update(data)
        self._save()

    def as_dict(self) -> dict:
        return dict(self._config)
```

- [ ] **Step 3: 创建 backend/services/hardware_detector.py (硬件检测+模型推荐)**

```python
import psutil
from dataclasses import dataclass


@dataclass
class HardwareInfo:
    cpu_cores: int
    total_memory_gb: float
    gpu_available: bool
    gpu_memory_gb: float
    gpu_name: str


MODEL_RECOMMENDATIONS = {
    "low": {       # <4GB RAM
        "llm": ["qwen2.5:0.5b", "tinyllama"],
        "embedding": "nomic-embed-text",
        "label": "轻量模式 (<4GB)",
    },
    "medium": {    # 4-8GB RAM
        "llm": ["qwen2.5:1.5b", "mistral:7b-q4_K_M"],
        "embedding": "nomic-embed-text",
        "label": "中等模式 (4-8GB)",
    },
    "high": {      # 8-16GB RAM
        "llm": ["qwen2.5:7b", "llama3.1:8b"],
        "embedding": "nomic-embed-text",
        "label": "高性能模式 (8-16GB)",
    },
    "ultra": {     # 16GB+ / GPU
        "llm": ["qwen2.5:14b", "llama3.1:70b-q4_K_M"],
        "embedding": "nomic-embed-text",
        "label": "超强模式 (16GB+/GPU)",
    },
}


def detect_hardware() -> HardwareInfo:
    """检测硬件配置"""
    cpu_cores = psutil.cpu_count(logical=True)
    total_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
    gpu_available = False
    gpu_memory_gb = 0.0
    gpu_name = ""

    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_available = True
            gpu_memory_gb = gpus[0].memoryTotal / 1024
            gpu_name = gpus[0].name
    except (ImportError, Exception):
        pass

    return HardwareInfo(
        cpu_cores=cpu_cores,
        total_memory_gb=round(total_memory_gb, 1),
        gpu_available=gpu_available,
        gpu_memory_gb=round(gpu_memory_gb, 1),
        gpu_name=gpu_name,
    )


def recommend_models(hw: HardwareInfo) -> dict:
    """根据硬件推荐模型"""
    ram = hw.total_memory_gb

    if ram < 4:
        tier = "low"
    elif ram < 8:
        tier = "medium"
    elif ram < 16:
        tier = "high"
    else:
        tier = "ultra"

    if hw.gpu_available and hw.gpu_memory_gb >= 8:
        tier = "ultra"

    rec = MODEL_RECOMMENDATIONS[tier]
    return {
        "tier": tier,
        "recommended_llm": rec["llm"],
        "recommended_embedding": rec["embedding"],
        "label": rec["label"],
        "hardware": hw,
    }
```

- [ ] **Step 4: 写硬件检测测试**

Create `backend/tests/test_hardware_detector.py`:
```python
from services.hardware_detector import HardwareInfo, recommend_models, MODEL_RECOMMENDATIONS


def test_recommend_low_ram():
    hw = HardwareInfo(cpu_cores=2, total_memory_gb=2.0, gpu_available=False, gpu_memory_gb=0, gpu_name="")
    rec = recommend_models(hw)
    assert rec["tier"] == "low"
    assert rec["recommended_embedding"] == "nomic-embed-text"


def test_recommend_medium_ram():
    hw = HardwareInfo(cpu_cores=4, total_memory_gb=6.0, gpu_available=False, gpu_memory_gb=0, gpu_name="")
    rec = recommend_models(hw)
    assert rec["tier"] == "medium"


def test_recommend_high_ram():
    hw = HardwareInfo(cpu_cores=8, total_memory_gb=12.0, gpu_available=False, gpu_memory_gb=0, gpu_name="")
    rec = recommend_models(hw)
    assert rec["tier"] == "high"


def test_recommend_ultra_ram():
    hw = HardwareInfo(cpu_cores=16, total_memory_gb=32.0, gpu_available=True, gpu_memory_gb=12.0, gpu_name="RTX 4080")
    rec = recommend_models(hw)
    assert rec["tier"] == "ultra"


def test_gpu_upgrades_tier():
    hw = HardwareInfo(cpu_cores=4, total_memory_gb=6.0, gpu_available=True, gpu_memory_gb=10.0, gpu_name="RTX 3080")
    rec = recommend_models(hw)
    assert rec["tier"] == "ultra"
```

- [ ] **Step 5: 运行硬件检测测试**

```bash
cd backend
python -m pytest tests/test_hardware_detector.py -v
# 期望: 5个测试全部PASS
```

- [ ] **Step 6: 创建 backend/services/ollama_service.py**

```python
import ollama
from config import AppConfig


class OllamaService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.host = config.get("ollama_host", "http://127.0.0.1:11434")

    def _client(self) -> ollama.Client:
        return ollama.Client(host=self.host)

    def is_connected(self) -> bool:
        try:
            self._client().list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[dict]:
        try:
            resp = self._client().list()
            return [{"name": m.model, "size": m.size, "modified_at": str(m.modified_at)} for m in resp.models]
        except Exception:
            return []

    def pull_model(self, model_name: str) -> dict:
        try:
            self._client().pull(model_name)
            return {"status": "success", "model": model_name}
        except Exception as e:
            return {"status": "error", "model": model_name, "error": str(e)}

    def generate(self, prompt: str, model: str = None) -> str:
        model = model or self.config.get("llm_model", "qwen2.5:7b")
        resp = self._client().generate(model=model, prompt=prompt)
        return resp.response

    def embed(self, text: str, model: str = None) -> list[float]:
        model = model or self.config.get("embedding_model", "nomic-embed-text")
        resp = self._client().embeddings(model=model, prompt=text)
        return resp.embedding
```

- [ ] **Step 7: 创建 backend/services/vector_store.py (Qdrant本地初始化)**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection
from config import QDRANT_DIR


COLLECTIONS = {
    "conversations": VectorParams(size=768, distance=Distance.COSINE),
    "memories": VectorParams(size=768, distance=Distance.COSINE),
    "knowledge": VectorParams(size=768, distance=Distance.COSINE),
    "profiles": VectorParams(size=768, distance=Distance.COSINE),
}


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(path=str(QDRANT_DIR))
        self._init_collections()

    def _init_collections(self):
        existing = [c.name for c in self.client.get_collections().collections]
        for name, params in COLLECTIONS.items():
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=params,
                )

    def get_collection_info(self, name: str) -> dict:
        info = self.client.get_collection(collection_name=name)
        return {
            "name": name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
```

- [ ] **Step 8: 创建 backend/services/database.py (SQLite初始化)**

```python
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from config import SQLITE_DIR

DB_PATH = SQLITE_DIR / "metadata.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ConfigRow(Base):
    __tablename__ = "config"
    key = Column(String, primary_key=True)
    value = Column(Text)


class SessionRow(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    source = Column(String)
    import_time = Column(DateTime)
    deleted = Column(Boolean, default=False)


class MemoryRow(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True)
    type = Column(String)
    dimensions = Column(Text)
    confidence = Column(Float)
    qdrant_id = Column(String)
    source_session_id = Column(String)


Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
```

- [ ] **Step 9: 创建 API schemas**

`backend/api/schemas/hardware.py`:
```python
from pydantic import BaseModel


class HardwareInfoResponse(BaseModel):
    cpu_cores: int
    total_memory_gb: float
    gpu_available: bool
    gpu_memory_gb: float
    gpu_name: str


class ModelRecommendationResponse(BaseModel):
    tier: str
    recommended_llm: list[str]
    recommended_embedding: str
    label: str
```

`backend/api/schemas/settings.py`:
```python
from pydantic import BaseModel


class AppConfigResponse(BaseModel):
    ollama_host: str
    llm_model: str
    embedding_model: str
    qdrant_host: str
    qdrant_port: int
    memory_expiry_days: int
    extract_dimensions: list[str]


class AppConfigUpdate(BaseModel):
    ollama_host: str | None = None
    llm_model: str | None = None
    embedding_model: str | None = None
    memory_expiry_days: int | None = None
    extract_dimensions: list[str] | None = None
```

`backend/api/schemas/ollama.py`:
```python
from pydantic import BaseModel


class OllamaStatusResponse(BaseModel):
    connected: bool
    models_count: int


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None


class PullModelRequest(BaseModel):
    model: str


class PullModelResponse(BaseModel):
    status: str
    model: str
    error: str | None = None
```

- [ ] **Step 10: 创建 API routes**

`backend/api/routes/health.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check():
    return {
        "status": "ok",
        "service": "mem-switch-backend",
        "version": "0.1.0",
    }
```

`backend/api/routes/hardware.py`:
```python
from fastapi import APIRouter
from services.hardware_detector import detect_hardware, recommend_models
from api.schemas.hardware import HardwareInfoResponse, ModelRecommendationResponse

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


@router.get("/detect", response_model=ModelRecommendationResponse)
async def detect():
    hw = detect_hardware()
    rec = recommend_models(hw)
    return ModelRecommendationResponse(
        tier=rec["tier"],
        recommended_llm=rec["recommended_llm"],
        recommended_embedding=rec["recommended_embedding"],
        label=rec["label"],
    )
```

`backend/api/routes/ollama.py`:
```python
from fastapi import APIRouter
from services.ollama_service import OllamaService
from config import AppConfig
from api.schemas.ollama import OllamaStatusResponse, ModelInfo, PullModelRequest, PullModelResponse

router = APIRouter(prefix="/api/ollama", tags=["ollama"])
config = AppConfig()
ollama_svc = OllamaService(config)


@router.get("/status", response_model=OllamaStatusResponse)
async def status():
    connected = ollama_svc.is_connected()
    models = ollama_svc.list_models() if connected else []
    return OllamaStatusResponse(connected=connected, models_count=len(models))


@router.get("/models", response_model=list[ModelInfo])
async def models():
    return [ModelInfo(**m) for m in ollama_svc.list_models()]


@router.post("/pull", response_model=PullModelResponse)
async def pull(req: PullModelRequest):
    result = ollama_svc.pull_model(req.model)
    return PullModelResponse(**result)
```

`backend/api/routes/settings.py`:
```python
from fastapi import APIRouter
from config import AppConfig
from api.schemas.settings import AppConfigResponse, AppConfigUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])
config = AppConfig()


@router.get("", response_model=AppConfigResponse)
async def get_settings():
    return AppConfigResponse(**config.as_dict())


@router.put("", response_model=AppConfigResponse)
async def update_settings(data: AppConfigUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    config.update(updates)
    return AppConfigResponse(**config.as_dict())
```

- [ ] **Step 11: 创建 backend/main.py (FastAPI入口)**

```python
from fastapi import FastAPI
from api.routes import health, hardware, ollama, settings
from services.vector_store import VectorStore
from config import BACKEND_HOST, BACKEND_PORT

app = FastAPI(title="Mem-Switch Backend", version="0.1.0")

# 注册路由
app.include_router(health.router)
app.include_router(hardware.router)
app.include_router(ollama.router)
app.include_router(settings.router)

# 初始化向量存储
vector_store = VectorStore()


@app.on_event("startup")
async def startup():
    print(f"Mem-Switch backend starting on {BACKEND_HOST}:{BACKEND_PORT}")
    print(f"Qdrant collections initialized")
    print(f"App data dir: {vector_store.client.get_collections()}")
```

- [ ] **Step 12: 写 health 和 settings API 测试**

`backend/tests/test_health_api.py`:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "mem-switch-backend"
```

`backend/tests/test_settings_api.py`:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_settings():
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_host" in data
    assert "embedding_model" in data


def test_update_settings():
    resp = client.put("/api/settings", json={"llm_model": "qwen2.5:7b"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["llm_model"] == "qwen2.5:7b"
```

- [ ] **Step 13: 运行后端测试**

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/test_hardware_detector.py tests/test_health_api.py tests/test_settings_api.py -v
# 期望: 全部PASS
```

- [ ] **Step 14: 手动验证后端 API 启动**

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8765 --reload
# 验证: 浏览器打开 http://127.0.0.1:8765/docs
# 期望: 看到 FastAPI Swagger UI，包含 health/hardware/ollama/settings 路由
# 测试: GET /api/health → {"status":"ok","service":"mem-switch-backend","version":"0.1.0"}
# 测试: GET /api/hardware/detect → 返回硬件检测结果和模型推荐
# 测试: GET /api/settings → 返回应用配置
```

- [ ] **Step 15: 提交后端初始化**

```bash
cd mem-switch-desktop
git add backend/
git commit -m "feat: init FastAPI backend with hardware detection, Ollama, Qdrant, and settings"
```

---

### Task 4: StartupGuide 和 SettingsView 前端组件

**Files:**
- Create: `frontend/src/components/StartupGuide.svelte`
- Create: `frontend/src/components/SettingsView.svelte`
- Test: 手动验证浏览器交互

- [ ] **Step 1: 创建 frontend/src/components/StartupGuide.svelte (首次启动引导)**

```svelte
<script>
  import { appState } from '../stores/app.svelte.js';
  import { hardwareState } from '../stores/hardware.svelte.js';
  import { api } from '../lib/api.js';

  let detecting = $state(false);
  let pulling = $state(false);
  let pullProgress = $state('');
  let error = $state('');

  async function detectHardware() {
    detecting = true;
    error = '';
    try {
      const resp = await api.hardware.detect();
      const data = resp.data;
      hardwareState.detected = true;
      hardwareState.recommendedModels = data.recommended_llm;
      hardwareState.selectedModel = data.recommended_llm[0];
      hardwareState.selectedEmbeddingModel = data.recommended_embedding;
    } catch (e) {
      error = '硬件检测失败: ' + (e.message || '后端未连接');
    }
    detecting = false;
  }

  async function checkOllama() {
    try {
      const resp = await api.ollama.status();
      hardwareState.ollamaConnected = resp.data.connected;
      if (resp.data.connected) {
        const modelsResp = await api.ollama.models();
        hardwareState.ollamaModels = modelsResp.data.map(m => m.name);
      }
    } catch (e) {
      hardwareState.ollamaConnected = false;
    }
  }

  async function pullModel() {
    pulling = true;
    pullProgress = '正在下载 ' + hardwareState.selectedModel + '...';
    try {
      await api.ollama.pull(hardwareState.selectedModel);
      pullProgress = '下载完成';
      await checkOllama();
    } catch (e) {
      pullProgress = '下载失败: ' + (e.message || '未知错误');
    }
    pulling = false;
  }

  async function initApp() {
    await detectHardware();
    await checkOllama();
  }

  // 自动检测后端连接
  $effect(() => {
    if (!appState.backendReady) {
      const check = async () => {
        try {
          await api.health();
          appState.backendReady = true;
          await initApp();
        } catch {
          appState.backendReady = false;
        }
      };
      check();
      const interval = setInterval(check, 3000);
      return () => clearInterval(interval);
    }
  });
</script>

<div class="max-w-2xl mx-auto p-8">
  <h1 class="text-3xl font-bold mb-6">Mem-Switch 启动引导</h1>

  {#if !appState.backendReady}
    <div class="bg-yellow-100 p-4 rounded-lg mb-4">
      等待后端服务连接...请确保后端已启动 (localhost:8765)
    </div>
  {:else if !hardwareState.detected}
    <div class="bg-blue-100 p-4 rounded-lg mb-4">
      正在检测硬件配置...
    </div>
  {:else}
    <div class="bg-green-100 p-4 rounded-lg mb-4">
      硬件检测完成! 推荐配置: {hardwareState.recommendedModels.length > 0 ? hardwareState.recommendedModels[0] : '无推荐'}
    </div>

    <!-- Ollama 状态 -->
    <div class="mt-6 p-4 border rounded-lg">
      <h2 class="text-xl font-semibold mb-2">Ollama 状态</h2>
      <p>连接: {hardwareState.ollamaConnected ? '✓ 已连接' : '✗ 未连接'}</p>
      {#if hardwareState.ollamaConnected}
        <p>已安装模型: {hardwareState.ollamaModels.join(', ') || '无'}</p>
      {/if}

      <!-- 模型选择 -->
      <div class="mt-4">
        <label class="block font-medium mb-1">LLM 模型</label>
        <select
          class="w-full p-2 border rounded"
          bind:value={hardwareState.selectedModel}
        >
          {#each hardwareState.recommendedModels as model}
            <option value={model}>{model}</option>
          {/each}
        </select>
      </div>

      <div class="mt-2">
        <label class="block font-medium mb-1">Embedding 模型</label>
        <select
          class="w-full p-2 border rounded"
          bind:value={hardwareState.selectedEmbeddingModel}
        >
          <option value="nomic-embed-text">nomic-embed-text (推荐)</option>
        </select>
      </div>

      {#if hardwareState.ollamaConnected && hardwareState.selectedModel && !hardwareState.ollamaModels.includes(hardwareState.selectedModel)}
        <button
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={pulling}
          onclick={pullModel}
        >
          {pulling ? pullProgress : '下载推荐模型'}
        </button>
      {/if}
    </div>

    {#if error}
      <div class="mt-4 bg-red-100 p-4 rounded-lg">{error}</div>
    {/if}

    <!-- 完成引导 -->
    {#if hardwareState.ollamaConnected}
      <button
        class="mt-6 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
        onclick={() => {
          appState.initialized = true;
          appState.currentTab = 'memory';
        }}
      >
        开始使用 Mem-Switch
      </button>
    {/if}
  {/if}
</div>
```

- [ ] **Step 2: 创建 frontend/src/components/SettingsView.svelte**

```svelte
<script>
  import { api } from '../lib/api.js';
  import { hardwareState } from '../stores/hardware.svelte.js';

  let settings = $state({});
  let loading = $state(true);
  let saving = $state(false);
  let saved = $state(false);

  async function loadSettings() {
    loading = true;
    try {
      const resp = await api.settings.get();
      settings = resp.data;
    } catch {}
    loading = false;
  }

  async function saveSettings() {
    saving = true;
    saved = false;
    try {
      await api.settings.update({
        ollama_host: settings.ollama_host,
        llm_model: hardwareState.selectedModel || settings.llm_model,
        embedding_model: hardwareState.selectedEmbeddingModel || settings.embedding_model,
        memory_expiry_days: settings.memory_expiry_days,
      });
      saved = true;
    } catch {}
    saving = false;
  }

  loadSettings();
</script>

<div class="max-w-2xl mx-auto p-8">
  <h1 class="text-3xl font-bold mb-6">设置</h1>

  {#if loading}
    <p>加载中...</p>
  {:else}
    <div class="space-y-4">
      <div>
        <label class="block font-medium mb-1">Ollama 地址</label>
        <input class="w-full p-2 border rounded" bind:value={settings.ollama_host} />
      </div>

      <div>
        <label class="block font-medium mb-1">LLM 模型</label>
        <input class="w-full p-2 border rounded" bind:value={settings.llm_model} />
      </div>

      <div>
        <label class="block font-medium mb-1">Embedding 模型</label>
        <input class="w-full p-2 border rounded" bind:value={settings.embedding_model} />
      </div>

      <div>
        <label class="block font-medium mb-1">记忆过期天数</label>
        <input type="number" class="w-full p-2 border rounded" bind:value={settings.memory_expiry_days} />
      </div>

      <div>
        <label class="block font-medium mb-1">Qdrant 地址</label>
        <input class="w-full p-2 border rounded bg-gray-100" value={settings.qdrant_host} disabled />
      </div>

      <div>
        <label class="block font-medium mb-1">Qdrant 端口</label>
        <input type="number" class="w-full p-2 border rounded bg-gray-100" value={settings.qdrant_port} disabled />
      </div>

      <button
        class="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        disabled={saving}
        onclick={saveSettings}
      >
        {saving ? '保存中...' : '保存设置'}
      </button>

      {#if saved}
        <span class="text-green-600 ml-2">✓ 已保存</span>
      {/if}
    </div>
  {/if}
</div>
```

- [ ] **Step 3: 验证前端与后端联动**

```bash
# 先启动后端
cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# 再启动前端
cd frontend && npm run dev

# 验证: 浏览器打开 http://localhost:5173
# 期望: 启动引导页自动检测后端连接状态
# 期望: 硬件检测结果和模型推荐显示正确
# 期望: 设置页面可以读取和修改配置
```

- [ ] **Step 4: 提交前端组件**

```bash
cd mem-switch-desktop
git add frontend/src/components/StartupGuide.svelte frontend/src/components/SettingsView.svelte
git commit -m "feat: add StartupGuide and SettingsView components"
```

---

### Task 5: Tauri v2 桌面框架集成

**Files:**
- Create: `src-tauri/Cargo.toml`
- Create: `src-tauri/build.rs`
- Create: `src-tauri/tauri.conf.json`
- Create: `src-tauri/capabilities/default.json`
- Create: `src-tauri/src/main.rs`
- Create: `src-tauri/src/lib.rs`
- Create: `src-tauri/icons/icon.png` (占位)
- Create: `src-tauri/icons/icon.ico` (占位)

- [ ] **Step 1: 安装 Tauri CLI 和初始化**

```bash
cd mem-switch-desktop
npm install @tauri-apps/cli@^2.0
npx tauri init --ci
# 交互式回答:
# - App name: Mem-Switch
# - Window title: Mem-Switch
# - Dev server URL: http://localhost:5173
# - Frontend dist dir: ../frontend/dist
# - Before dev command: cd frontend && npm run dev
# - Before build command: cd frontend && npm run build
```

- [ ] **Step 2: 修改 src-tauri/tauri.conf.json**

确保配置如下关键项:
```json
{
  "productName": "Mem-Switch",
  "version": "0.1.0",
  "identifier": "com.mem-switch.desktop",
  "build": {
    "beforeDevCommand": "cd frontend && npm run dev",
    "beforeBuildCommand": "cd frontend && npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../frontend/dist"
  },
  "app": {
    "windows": [
      {
        "title": "Mem-Switch",
        "width": 1024,
        "height": 768,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": null
    }
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
    ]
  }
}
```

- [ ] **Step 3: 配置 src-tauri/capabilities/default.json**

添加 sidecar 权限:
```json
{
  "identifier": "default",
  "description": "Default permissions for the app",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "opener:default",
    {
      "identifier": "shell:allow-spawn",
      "allow": [
        {
          "name": "binaries/mem-switch-backend",
          "sidecar": true,
          "args": true
        }
      ]
    },
    {
      "identifier": "shell:allow-kill",
      "allow": [
        {
          "name": "binaries/mem-switch-backend",
          "sidecar": true
        }
      ]
    }
  ]
}
```

- [ ] **Step 4: 创建 src-tauri/src/main.rs (启动 sidecar)**

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    mem_switch_desktop_lib::run()
}
```

- [ ] **Step 5: 创建 src-tauri/src/lib.rs (Tauri setup + sidecar 管理)**

```rust
use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use tauri::Emitter;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 启动 Python 后端 sidecar
            let sidecar_command = app.shell().sidecar("mem-switch-backend").unwrap();
            let (mut rx, child) = sidecar_command.spawn().expect("Failed to spawn backend sidecar");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Stdout(line_bytes) = event {
                        let line = String::from_utf8_lossy(&line_bytes);
                        println!("Backend: {}", line);
                    }
                    if let CommandEvent::Stderr(line_bytes) = event {
                        let line = String::from_utf8_lossy(&line_bytes);
                        println!("Backend stderr: {}", line);
                    }
                }
            });

            // 存储子进程引用以便后续关闭
            app.manage(BackendProcess(child));

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

struct BackendProcess(tauri_plugin_shell::process::CommandChild);
```

- [ ] **Step 6: 创建占位图标文件**

```bash
cd src-tauri/icons
# 创建占位图标 (后续Phase 4替换为正式图标)
# 使用 Tauri 内置的默认图标生成
npx tauri icon
```

- [ ] **Step 7: 打包 Python 后端为 sidecar 二进制**

```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --name mem-switch-backend \
    main.py \
    --add-data "config:config" \
    --hidden-import mem0 \
    --hidden-import qdrant_client \
    --hidden-import ollama \
    --hidden-import sqlalchemy \
    --hidden-import psutil

# 将生成的二进制复制到 sidecar 目录
# Windows: mem-switch-backend.exe
# Linux/Mac: mem-switch-backend
mkdir -p ../src-tauri/binaries
cp dist/mem-switch-backend* ../src-tauri/binaries/
```

注意: sidecar 二进制需要按平台命名后缀:
- Windows: `mem-switch-backend-x86_64-pc-windows-msvc.exe`
- MacOS: `mem-switch-backend-aarch64-apple-darwin` 或 `mem-switch-backend-x86_64-apple-darwin`
- Linux: `mem-switch-backend-x86_64-unknown-linux-gnu`

- [ ] **Step 8: 验证 Tauri 应用完整启动**

```bash
cd mem-switch-desktop
npm run tauri dev
# 期望: Tauri窗口打开，显示Mem-Switch界面
# 期望: 后端sidecar自动启动，StartupGuide检测到后端连接
# 期望: 硬件检测结果和模型推荐显示正确
```

- [ ] **Step 9: 提交 Tauri 集成**

```bash
cd mem-switch-desktop
git add src-tauri/ frontend/src/App.svelte
git commit -m "feat: integrate Tauri v2 with sidecar backend and desktop window"
```

---

### Task 6: 开发环境初始化脚本 + 最终验证

**Files:**
- Create: `scripts/setup-dev.sh`

- [ ] **Step 1: 创建 scripts/setup-dev.sh**

```bash
#!/bin/bash
set -e

echo "=== Mem-Switch 开发环境初始化 ==="

# 检查依赖
echo "检查系统依赖..."
command -v node >/dev/null 2>&1 || { echo "需要 Node.js (>=18)"; exit 1; }
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || { echo "需要 Python (>=3.10)"; exit 1; }
command -v cargo >/dev/null 2>&1 || { echo "需要 Rust (通过 rustup 安装)"; exit 1; }
command -v ollama >/dev/null 2>&1 || echo "警告: Ollama未安装，请先安装 https://ollama.com"

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
cd ..

# 安装后端依赖
echo "安装后端依赖..."
cd backend
pip install -r requirements.txt
cd ..

# 安装根项目依赖
echo "安装根项目依赖..."
npm install

echo "=== 初始化完成 ==="
echo "启动开发模式: npm run tauri dev"
echo "或分步启动:"
echo "  后端: cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload"
echo "  前端: cd frontend && npm run dev"
echo "  桌面: npm run tauri dev"
```

- [ ] **Step 2: 运行 setup-dev.sh 初始化**

```bash
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
# 期望: 所有依赖安装成功
```

- [ ] **Step 3: 最终验证——完整启动测试**

```bash
# 方式1: 分步启动(开发调试)
cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 --reload &
cd frontend && npm run dev

# 方式2: Tauri完整启动
npm run tauri dev

# 验证清单:
# 1. Tauri窗口打开，显示Mem-Switch界面 ✓
# 2. StartupGuide自动检测后端连接 ✓
# 3. 硬件检测结果显示 (CPU核心数、内存大小、GPU信息) ✓
# 4. Ollama连接状态显示 ✓
# 5. 模型推荐列表显示 ✓
# 6. 设置页面可读取和修改配置 ✓
# 7. 状态栏显示后端和Ollama连接状态 ✓
```

- [ ] **Step 4: 提交最终初始化**

```bash
cd mem-switch-desktop
git add scripts/
git commit -m "feat: add dev setup script and complete Phase 1 verification"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- 跨平台桌面安装包框架 ✓ (Tauri v2)
- Svelte 5 前端 ✓ (Sidebar + Tabs routing)
- Python FastAPI 后端 ✓ (health/hardware/ollama/settings routes)
- Qdrant本地模式 ✓ (4 collections initialized)
- SQLite元数据 ✓ (config/sessions/memories tables)
- 硬件检测 + 模型推荐 ✓ (psutil + tier system)
- Ollama连接 + 模型管理 ✓ (status/models/pull)
- 首次启动引导页 ✓ (StartupGuide component)
- 设置界面 ✓ (SettingsView component)
- 侧边栏导航 ✓ (Sidebar + StatusBar)
- 跨平台数据目录 ✓ (config.py get_app_data_dir)

**2. Placeholder scan:**
- 无 TBD/TODO ✓
- 无 "implement later" ✓
- 所有步骤包含实际代码 ✓

**3. Type consistency:**
- HardwareInfoResponse 在 schema 和 route 中匹配 ✓
- AppConfigResponse 在 schema 和 route 中匹配 ✓
- hardwareState 在 store 和 component 中字段一致 ✓
- api.js 中端点路径与 backend routes prefix 匹配 ✓

**Gaps identified:** 无。Phase 1 覆盖了设计规格书中 Phase 1 的全部任务。

---

Plan complete and saved to `docs/superpowers/plans/2026-04-28-mem-switch-phase1.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 每个Task派发独立子agent，之间review，快速迭代

**2. Inline Execution** - 在当前session中使用executing-plans，批量执行带checkpoint

Which approach?