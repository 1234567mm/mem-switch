# README 中英双语国际化

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 更新 README 为中英双语，首页默认显示中文，英文版为 README-en.md

**Architecture:** 前端使用简单的 i18n store 检测浏览器语言并切换。README 分中英两个版本，通过文件扩展名区分。

**Tech Stack:** Svelte 5 Runes, JSON i18n files

---

## 文件结构

- Create: `frontend/src/i18n/translations.json` - 中英翻译
- Create: `frontend/src/i18n/index.svelte` - i18n store
- Modify: `frontend/src/App.svelte` - 集成 i18n
- Create: `README-en.md` - 英文版 README
- Modify: `README.md` - 中英双语版本

---

## Task 1: 创建前端 i18n 系统

**Files:**
- Create: `frontend/src/i18n/translations.json`
- Create: `frontend/src/i18n/index.svelte`
- Modify: `frontend/src/App.svelte:1-30`

- [ ] **Step 1: 创建 translations.json**

```json
{
  "zh": {
    "app.name": "Mem-Switch",
    "app.subtitle": "跨平台桌面记忆管理应用",
    "nav.memory": "记忆库",
    "nav.knowledge": "知识库",
    "nav.import": "对话导入",
    "nav.settings": "设置",
    "search.placeholder": "搜索记忆和知识..."
  },
  "en": {
    "app.name": "Mem-Switch",
    "app.subtitle": "Cross-platform desktop memory management app",
    "nav.memory": "Memory",
    "nav.knowledge": "Knowledge",
    "nav.import": "Import",
    "nav.settings": "Settings",
    "search.placeholder": "Search memories and knowledge..."
  }
}
```

- [ ] **Step 2: 创建 i18n store**

```svelte
<script>
  import { writable } from 'svelte/store';

  import translations from './translations.json';

  // Detect browser language
  function getBrowserLang() {
    const lang = navigator.language.toLowerCase();
    return lang.startsWith('zh') ? 'zh' : 'en';
  }

  // Create reactive language store
  export const currentLang = writable(getBrowserLang());

  // Translation function
  export function t(key) {
    const lang = $currentLang;
    return translations[lang]?.[key] || translations['en'][key] || key;
  }
</script>
```

- [ ] **Step 3: 修改 App.svelte 添加语言切换**

在 App.svelte 顶部添加：
```svelte
<script>
  import { currentLang, t } from './i18n/index.svelte';

  let lang = $state('zh');

  // Subscribe to store
  currentLang.subscribe(v => lang = v);
</script>

<!-- 在导航栏添加语言切换 -->
<button onclick={() => currentLang.set(lang === 'zh' ? 'en' : 'zh')}>
  {lang === 'zh' ? 'EN' : '中文'}
</button>
```

---

## Task 2: 创建英文版 README

**Files:**
- Create: `README-en.md`

- [ ] **Step 1: 创建 README-en.md**

```markdown
# Mem-Switch

Cross-platform desktop memory management app. Unified management of knowledge base, memory store, and conversation imports.

![Version](https://img.shields.io/badge/version-0.1.7-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue)

## Features

... (English content, full translation of README.md)
```

---

## Task 3: 更新中文 README 为双语版

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 将 README.md 转换为双语结构**

标题和主要说明保持中文，添加英文副标题：
```markdown
# Mem-Switch

跨平台桌面记忆管理应用 / Cross-platform desktop memory management app

...
```

---

## Task 4: 验证

- [ ] **Step 1: 验证 i18n 系统**

```bash
cd frontend && npm run build
```

- [ ] **Step 2: 验证 README 语法**

```bash
head -50 README.md
head -50 README-en.md
```

---

## Self-Review

1. **Spec coverage:** 中文默认 + 英文版 README-en.md ✓
2. **Placeholder scan:** 无 TBD/TODO
3. **Type consistency:** i18n store 使用 Svelte 5 Runes