<script>
  import { appState } from '../stores/app.svelte.js';
  import { hardwareState } from '../stores/hardware.svelte.js';
  import { addToast } from '../stores/toast.svelte.js';
  import { api } from '../lib/api.js';

  let detecting = $state(false);
  let pulling = $state(false);
  let pullProgress = $state('');
  let selectedTier = $state('medium');

  const tiers = [
    { id: 'low', label: '轻量模式', desc: '<4GB内存', model: 'qwen2.5:0.5b' },
    { id: 'medium', label: '中等模式', desc: '4-8GB内存', model: 'qwen2.5:1.5b' },
    { id: 'high', label: '高性能', desc: '8-16GB内存', model: 'qwen2.5:7b' },
    { id: 'ultra', label: '超强模式', desc: '16GB+/GPU', model: 'qwen2.5:14b' },
  ];

  async function detectHardware() {
    detecting = true;
    try {
      const resp = await api.hardware.detect();
      const data = resp.data;
      hardwareState.detected = true;
      hardwareState.selectedModel = data.recommended_llm?.[0] || '';
      hardwareState.selectedEmbeddingModel = data.recommended_embedding || 'nomic-embed-text';
      selectedTier = data.tier || 'medium';
      addToast('硬件检测完成', 'success');
    } catch (e) {
      addToast('硬件检测失败: ' + (e.message || '后端未连接'), 'error');
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
        addToast('Ollama 已连接', 'success');
      }
    } catch {
      hardwareState.ollamaConnected = false;
      addToast('Ollama 未连接', 'warning');
    }
  }

  async function pullModel() {
    pulling = true;
    pullProgress = '下载中...';
    try {
      await api.ollama.pull(hardwareState.selectedModel);
      pullProgress = '下载完成';
      addToast('模型下载成功', 'success');
      await checkOllama();
    } catch (e) {
      pullProgress = '下载失败';
      addToast('模型下载失败: ' + (e.message || '未知错误'), 'error');
    }
    pulling = false;
  }

  // 自动检测
  $effect(() => {
    if (!appState.backendReady) return;
    detectHardware();
    checkOllama();
  });

  function selectTier(tier) {
    selectedTier = tier.id;
    hardwareState.selectedModel = tier.model;
  }
</script>

<div class="max-w-3xl mx-auto p-8">
  <!-- Header -->
  <div class="text-center mb-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-2">欢迎使用 Mem-Switch</h1>
    <p class="text-gray-500">在开始之前，让我们完成一些设置</p>
  </div>

  {#if !appState.backendReady}
    <div class="card p-6 text-center">
      <div class="text-amber-500 mb-4 text-5xl">⏳</div>
      <h2 class="text-xl font-semibold text-gray-700 mb-2">等待后端服务</h2>
      <p class="text-gray-500">请确保后端已启动 (localhost:8765)</p>
    </div>
  {:else}
    <div class="space-y-6">
      <!-- Step 1: Ollama 状态 -->
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">1</div>
          <h2 class="text-xl font-semibold text-gray-800">Ollama 连接状态</h2>
        </div>

        <div class="ml-11">
          <div class="flex items-center gap-3 mb-4">
            <span class="w-3 h-3 rounded-full {hardwareState.ollamaConnected ? 'bg-green-500' : 'bg-red-500'}"></span>
            <span class="font-medium {hardwareState.ollamaConnected ? 'text-green-600' : 'text-red-600'}">
              {hardwareState.ollamaConnected ? '已连接' : '未连接'}
            </span>
          </div>

          {#if hardwareState.ollamaConnected && hardwareState.ollamaModels.length > 0}
            <p class="text-sm text-gray-500 mb-2">已安装模型:</p>
            <div class="flex flex-wrap gap-2">
              {#each hardwareState.ollamaModels as model}
                <span class="badge badge-info">{model}</span>
              {/each}
            </div>
          {:else if !hardwareState.ollamaConnected}
            <p class="text-sm text-amber-600 mt-2">
              请确保 Ollama 已启动: <code class="bg-gray-100 px-2 py-1 rounded">ollama serve</code>
            </p>
          {/if}

          <button
            class="btn-secondary mt-4"
            onclick={() => { checkOllama(); }}
            disabled={detecting}
          >
            {detecting ? '检测中...' : '重新检测'}
          </button>
        </div>
      </div>

      <!-- Step 2: 模型选择 -->
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">2</div>
          <h2 class="text-xl font-semibold text-gray-800">选择 LLM 模型</h2>
        </div>

        <div class="ml-11">
          {#if hardwareState.detected}
            <p class="text-sm text-blue-600 mb-4 flex items-center gap-2">
              <span>✓</span> 检测到硬件配置，已推荐合适模型
            </p>
          {/if}

          <div class="grid grid-cols-2 gap-3 mb-6">
            {#each tiers as tier}
              <button
                class="p-4 border rounded-xl text-left transition-all {selectedTier === tier.id ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}"
                onclick={() => selectTier(tier)}
              >
                <div class="font-semibold text-gray-800">{tier.label}</div>
                <div class="text-sm text-gray-500">{tier.desc}</div>
              </button>
            {/each}
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">选择模型</label>
            <input
              class="input bg-gray-50"
              value={hardwareState.selectedModel}
              readonly
            />
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Embedding 模型</label>
            <input
              class="input bg-gray-50"
              value={hardwareState.selectedEmbeddingModel}
              readonly
            />
          </div>

          {#if hardwareState.ollamaConnected && hardwareState.selectedModel && !hardwareState.ollamaModels.includes(hardwareState.selectedModel)}
            <button
              class="btn-primary flex items-center gap-2"
              disabled={pulling}
              onclick={pullModel}
            >
              {#if pulling}
                <span class="animate-spin">⟳</span> {pullProgress}
              {:else}
                <span>↓</span> 下载模型
              {/if}
            </button>
          {/if}
        </div>
      </div>

      <!-- Step 3: 开始使用 -->
      {#if hardwareState.ollamaConnected}
        <div class="card p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-semibold text-gray-800">准备就绪!</h3>
              <p class="text-sm text-gray-500">点击下方按钮开始使用 Mem-Switch</p>
            </div>
            <button
              class="btn-primary px-8 py-3 text-lg"
              onclick={() => {
                appState.initialized = true;
                appState.currentTab = 'memory';
                addToast('设置完成，开始使用吧！', 'success');
              }}
            >
              开始使用 →
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>