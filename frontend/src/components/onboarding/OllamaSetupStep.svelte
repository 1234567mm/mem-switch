<script>
  let { onNext, onPrev, ollamaUrl, ollamaConnected, onSetOllamaUrl } = $props();

  let inputUrl = $state(ollamaUrl || 'http://localhost:11434');
  let testing = $state(false);

  async function handleTestConnection() {
    testing = true;
    onSetOllamaUrl(inputUrl);
    await new Promise(r => setTimeout(r, 1000));
    testing = false;
  }
</script>

<div class="py-4">
  <h2 class="text-2xl font-bold text-gray-800 mb-2">配置 Ollama</h2>
  <p class="text-gray-600 mb-6">Mem-Switch 使用 Ollama 运行本地 AI 模型</p>

  <div class="max-w-md mx-auto">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      Ollama 地址
    </label>
    <div class="flex gap-2 mb-4">
      <input
        type="text"
        class="flex-1 border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
        bind:value={inputUrl}
        placeholder="http://localhost:11434"
      />
      <button
        class="btn-secondary"
        onclick={handleTestConnection}
        disabled={testing}
      >
        {testing ? '测试中...' : '测试'}
      </button>
    </div>

    {#if ollamaConnected}
      <div class="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
        <span class="text-xl mr-2">✓</span>
        Ollama 已连接！
      </div>
    {:else}
      <div class="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800">
        <span class="text-xl mr-2">⚠️</span>
        未连接到 Ollama
        <ul class="mt-2 text-sm list-disc list-inside">
          <li>确保 Ollama 已安装并运行</li>
          <li>检查地址是否正确</li>
          <li>WSL 用户请使用 http://localhost:11434</li>
        </ul>
      </div>
    {/if}

    <div class="mt-6 p-4 bg-gray-50 rounded-lg">
      <p class="text-sm text-gray-600 mb-2">还没有安装 Ollama？</p>
      <code class="text-xs bg-gray-200 px-2 py-1 rounded">
        curl -fsSL https://ollama.com/install.sh | sh
      </code>
    </div>
  </div>

  <div class="flex justify-between mt-8">
    <button class="btn-secondary" onclick={onPrev}>← 返回</button>
    <button
      class="btn-primary"
      onclick={onNext}
      disabled={!ollamaConnected}
    >
      下一步 →
    </button>
  </div>
</div>