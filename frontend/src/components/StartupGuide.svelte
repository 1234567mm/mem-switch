<script>
  import { appState } from '../stores/app.svelte.js';
  import { hardwareState } from '../stores/hardware.svelte.js';
  import { api } from '../lib/api.js';

  let detecting = $state(false);
  let pulling = $state(false);
  let pullProgress = $state('');
  let error = $state('');
  let selectedTier = $state('medium');

  const tiers = [
    { id: 'low', label: '轻量模式', desc: '<4GB内存' },
    { id: 'medium', label: '中等模式', desc: '4-8GB内存' },
    { id: 'high', label: '高性能', desc: '8-16GB内存' },
    { id: 'ultra', label: '超强模式', desc: '16GB+/GPU' },
  ];

  async function detectHardware() {
    detecting = true;
    error = '';
    try {
      const resp = await api.hardware.detect();
      const data = resp.data;
      hardwareState.detected = true;
      hardwareState.selectedModel = data.recommended_llm?.[0] || '';
      hardwareState.selectedEmbeddingModel = data.recommended_embedding || 'nomic-embed-text';
      selectedTier = data.tier || 'medium';
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
    } catch {
      hardwareState.ollamaConnected = false;
    }
  }

  async function pullModel() {
    pulling = true;
    pullProgress = '下载中...';
    try {
      await api.ollama.pull(hardwareState.selectedModel);
      pullProgress = '下载完成';
      await checkOllama();
    } catch (e) {
      pullProgress = '下载失败: ' + (e.message || '未知错误');
    }
    pulling = false;
  }

  // 自动检测
  $effect(() => {
    if (!appState.backendReady) return;
    detectHardware();
    checkOllama();
  });
</script>

<div class="max-w-2xl mx-auto p-8">
  <h1 class="text-3xl font-bold mb-6">Mem-Switch 启动引导</h1>

  {#if !appState.backendReady}
    <div class="bg-yellow-100 p-4 rounded-lg mb-4">
      等待后端服务连接...请确保后端已启动 (localhost:8765)
    </div>
  {:else}
    <div class="space-y-6">
      <!-- Ollama 状态 -->
      <div class="p-4 border rounded-lg">
        <h2 class="text-xl font-semibold mb-3">Ollama 状态</h2>
        <p class="mb-2">
          连接状态: <span class={hardwareState.ollamaConnected ? 'text-green-600' : 'text-red-600'}>
            {hardwareState.ollamaConnected ? '✓ 已连接' : '✗ 未连接'}
          </span>
        </p>
        {#if hardwareState.ollamaConnected && hardwareState.ollamaModels.length > 0}
          <p>已安装模型: {hardwareState.ollamaModels.join(', ')}</p>
        {/if}
        {#if !hardwareState.ollamaConnected}
          <p class="text-sm text-gray-600 mt-1">请确保 Ollama 已启动: <code>ollama serve</code></p>
        {/if}
      </div>

      <!-- 模型选择 -->
      <div class="p-4 border rounded-lg">
        <h2 class="text-xl font-semibold mb-3">选择 LLM 模型</h2>

        {#if hardwareState.detected}
          <p class="mb-3 text-sm text-gray-600">检测到硬件配置，已推荐合适模型</p>
        {/if}

        <div class="grid grid-cols-2 gap-2 mb-4">
          {#each tiers as tier}
            <button
              class="p-3 border rounded-lg text-left hover:bg-gray-50 {selectedTier === tier.id ? 'border-blue-500 bg-blue-50' : ''}"
              onclick={() => {
                selectedTier = tier.id;
                if (tier.id === 'low') hardwareState.selectedModel = 'qwen2.5:0.5b';
                else if (tier.id === 'medium') hardwareState.selectedModel = 'qwen2.5:1.5b';
                else if (tier.id === 'high') hardwareState.selectedModel = 'qwen2.5:7b';
                else hardwareState.selectedModel = 'qwen2.5:14b';
              }}
            >
              <div class="font-medium">{tier.label}</div>
              <div class="text-sm text-gray-500">{tier.desc}</div>
            </button>
          {/each}
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium mb-1">Embedding 模型</label>
          <input
            class="w-full p-2 border rounded bg-gray-100"
            value={hardwareState.selectedEmbeddingModel}
            readonly
          />
        </div>

        {#if hardwareState.ollamaConnected && hardwareState.selectedModel && !hardwareState.ollamaModels.includes(hardwareState.selectedModel)}
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={pulling}
            onclick={pullModel}
          >
            {pulling ? pullProgress : '下载推荐模型'}
          </button>
        {/if}
      </div>

      {#if error}
        <div class="bg-red-100 p-4 rounded-lg text-red-700">{error}</div>
      {/if}

      {#if hardwareState.ollamaConnected}
        <button
          class="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 text-lg"
          onclick={() => {
            appState.initialized = true;
            appState.currentTab = 'memory';
          }}
        >
          开始使用 Mem-Switch
        </button>
      {/if}
    </div>
  {/if}
</div>