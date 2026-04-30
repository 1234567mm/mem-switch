<script>
  let { onNext, onPrev, selectedModel, availableModels, onSelectModel, onPullModel } = $props();

  let pullingModel = $state(null);
  let pullProgress = $state('');

  const recommendedModels = [
    { id: 'qwen2.5:0.5b', label: 'Qwen 2.5 (0.5B)', desc: '轻量快速，适合基础任务' },
    { id: 'qwen2.5:1.5b', label: 'Qwen 2.5 (1.5B)', desc: '平衡性能和速度' },
    { id: 'qwen2.5:7b', label: 'Qwen 2.5 (7B)', desc: '高质量，需要较多内存' },
    { id: 'llama3.2:1b', label: 'Llama 3.2 (1B)', desc: 'Meta 最新轻量模型' },
    { id: 'llama3.2:3b', label: 'Llama 3.2 (3B)', desc: '性能优秀' },
  ];

  async function handlePullModel(modelName) {
    pullingModel = modelName;
    pullProgress = `正在下载 ${modelName}...`;
    try {
      await onPullModel(modelName);
      pullProgress = '下载完成！';
    } catch (e) {
      pullProgress = '下载失败: ' + e.message;
    }
    pullingModel = null;
  }
</script>

<div class="py-4">
  <h2 class="text-2xl font-bold text-gray-800 mb-2">选择 AI 模型</h2>
  <p class="text-gray-600 mb-6">选择一个适合您硬件配置的模型</p>

  <div class="grid gap-3 max-w-2xl mx-auto">
    {#each recommendedModels as model}
      <button
        class="p-4 border-2 rounded-xl text-left transition-all hover:border-blue-300 {selectedModel === model.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}"
        onclick={() => onSelectModel(model.id)}
      >
        <div class="flex justify-between items-center">
          <div>
            <div class="font-semibold text-gray-800">{model.label}</div>
            <div class="text-sm text-gray-500">{model.desc}</div>
          </div>
          {#if availableModels.includes(model.id)}
            <span class="text-green-600 text-sm">已安装 ✓</span>
          {:else}
            <button
              class="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              onclick={(e) => { e.stopPropagation(); handlePullModel(model.id); }}
              disabled={pullingModel !== null}
            >
              {#if pullingModel === model.id}
                下载中...
              {:else}
                下载
              {/if}
            </button>
          {/if}
        </div>
      </button>
    {/each}
  </div>

  {#if pullProgress}
    <div class="mt-4 p-3 bg-blue-50 text-blue-800 rounded-lg text-sm">
      {pullProgress}
    </div>
  {/if}

  <div class="flex justify-between mt-8">
    <button class="btn-secondary" onclick={onPrev}>← 返回</button>
    <button
      class="btn-primary"
      onclick={onNext}
      disabled={!selectedModel}
    >
      下一步 →
    </button>
  </div>
</div>