<script>
  import { api } from '../lib/api.js';
  import { hardwareState } from '../stores/hardware.svelte.js';

  let settings = $state({
    ollama_host: 'http://127.0.0.1:11434',
    llm_model: '',
    embedding_model: 'nomic-embed-text',
    memory_expiry_days: 180,
    qdrant_host: 'localhost',
    qdrant_port: 6333,
  });
  let loading = $state(true);
  let saving = $state(false);
  let saved = $state(false);

  async function loadSettings() {
    loading = true;
    try {
      const resp = await api.settings.get();
      settings = { ...resp.data };
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
      setTimeout(() => saved = false, 2000);
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
        <label class="block text-sm font-medium mb-1">Ollama 地址</label>
        <input class="w-full p-2 border rounded" bind:value={settings.ollama_host} />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">LLM 模型</label>
        <input class="w-full p-2 border rounded" bind:value={hardwareState.selectedModel} />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Embedding 模型</label>
        <input class="w-full p-2 border rounded" bind:value={hardwareState.selectedEmbeddingModel} />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">记忆过期天数</label>
        <input type="number" class="w-full p-2 border rounded" bind:value={settings.memory_expiry_days} />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Qdrant 模式</label>
        <p class="text-sm text-gray-500">本地嵌入模式 (数据存储在 ~/.local/share/Mem-Switch/qdrant_storage)</p>
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