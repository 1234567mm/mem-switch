<script>
  import {
    onboardingState,
    steps,
    nextStep,
    prevStep,
    goToStep,
    checkOllamaConnection,
    setOllamaUrl,
    selectModel,
    selectEmbeddingModel,
    markDataImported,
    completeOnboarding,
  } from '../stores/onboarding.svelte.js';
  import { addToast } from '../stores/toast.svelte.js';
  import { api } from '../lib/api.js';

  let ollamaUrlInput = $state('http://localhost:11434');
  let pullingModel = $state(false);
  let pullProgress = $state('');

  const recommendedModels = [
    { id: 'qwen2.5:0.5b', label: 'Qwen 2.5 (0.5B)', desc: '轻量快速，适合基础任务' },
    { id: 'qwen2.5:1.5b', label: 'Qwen 2.5 (1.5B)', desc: '平衡性能和速度' },
    { id: 'qwen2.5:7b', label: 'Qwen 2.5 (7B)', desc: '高质量，需要较多内存' },
    { id: 'llama3.2:1b', label: 'Llama 3.2 (1B)', desc: 'Meta 最新轻量模型' },
    { id: 'llama3.2:3b', label: 'Llama 3.2 (3B)', desc: '性能优秀' },
  ];

  async function handlePullModel(modelName) {
    pullingModel = true;
    pullProgress = `正在下载 ${modelName}...`;
    try {
      await api.ollama.pull(modelName);
      pullProgress = '下载完成！';
      addToast('模型下载成功', 'success');
      await checkOllamaConnection();
    } catch (e) {
      pullProgress = '下载失败';
      addToast('模型下载失败：' + e.message, 'error');
    }
    pullingModel = false;
  }

  function handleComplete() {
    completeOnboarding();
    addToast('设置完成！开始使用 Mem-Switch 吧', 'success');
  }
</script>

<div class="fixed inset-0 bg-gradient-to-br from-blue-50 to-indigo-100 z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-2xl shadow-xl max-w-4xl w-full overflow-hidden">
    <!-- Header with Progress -->
    <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
      <div class="flex items-center justify-between mb-4">
        <h1 class="text-2xl font-bold">欢迎使用 Mem-Switch</h1>
        <span class="text-sm opacity-80">步骤 {onboardingState.currentStep + 1} / {steps.length}</span>
      </div>

      <!-- Progress Bar -->
      <div class="flex items-center gap-2">
        {#each steps as step, i}
          <button
            class="flex-1 h-2 rounded-full transition-all {i <= onboardingState.currentStep ? 'bg-white' : 'bg-white/30'}"
            onclick={() => goToStep(i)}
            disabled={i > onboardingState.currentStep}
          />
        {/each}
      </div>
    </div>

    <!-- Step Content -->
    <div class="p-8">
      {#if onboardingState.currentStep === 0}
        <!-- Step 0: Welcome -->
        <div class="text-center py-8">
          <div class="text-6xl mb-6">🎉</div>
          <h2 class="text-3xl font-bold text-gray-800 mb-4">欢迎使用 Mem-Switch</h2>
          <p class="text-gray-600 mb-8 max-w-md mx-auto">
            您的 AI 对话记忆管理助手
            <br />
            将 AI 对话转化为可管理的记忆知识库
          </p>

          <div class="grid grid-cols-3 gap-4 max-w-2xl mx-auto mb-8">
            <div class="p-4 bg-blue-50 rounded-xl">
              <div class="text-3xl mb-2">📥</div>
              <div class="font-medium text-gray-800">导入对话</div>
              <div class="text-sm text-gray-500 mt-1">支持多个 AI 平台</div>
            </div>
            <div class="p-4 bg-green-50 rounded-xl">
              <div class="text-3xl mb-2">🧠</div>
              <div class="font-medium text-gray-800">提取记忆</div>
              <div class="text-sm text-gray-500 mt-1">AI 自动分析提取</div>
            </div>
            <div class="p-4 bg-purple-50 rounded-xl">
              <div class="text-3xl mb-2">🔍</div>
              <div class="font-medium text-gray-800">智能搜索</div>
              <div class="text-sm text-gray-500 mt-1">向量语义搜索</div>
            </div>
          </div>

          <button class="btn-primary px-8 py-3 text-lg" onclick={nextStep}>
            开始设置 →
          </button>
        </div>

      {:else if onboardingState.currentStep === 1}
        <!-- Step 1: Ollama Configuration -->
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
                bind:value={ollamaUrlInput}
                placeholder="http://localhost:11434"
              />
              <button
                class="btn-secondary"
                onclick={() => { setOllamaUrl(ollamaUrlInput); }}
              >
                连接
              </button>
            </div>

            {#if onboardingState.ollamaConnected}
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
            <button class="btn-secondary" onclick={prevStep}>← 返回</button>
            <button
              class="btn-primary"
              onclick={nextStep}
              disabled={!onboardingState.ollamaConnected}
            >
              下一步 →
            </button>
          </div>
        </div>

      {:else if onboardingState.currentStep === 2}
        <!-- Step 2: Model Selection -->
        <div class="py-4">
          <h2 class="text-2xl font-bold text-gray-800 mb-2">选择 AI 模型</h2>
          <p class="text-gray-600 mb-6">选择一个适合您硬件配置的模型</p>

          <div class="grid gap-3 max-w-2xl">
            {#each recommendedModels as model}
              <button
                class="p-4 border-2 rounded-xl text-left transition-all hover:border-blue-300 {onboardingState.selectedModel === model.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}"
                onclick={() => selectModel(model.id)}
              >
                <div class="flex justify-between items-center">
                  <div>
                    <div class="font-semibold text-gray-800">{model.label}</div>
                    <div class="text-sm text-gray-500">{model.desc}</div>
                  </div>
                  {#if onboardingState.availableModels.includes(model.id)}
                    <span class="text-green-600 text-sm">已安装</span>
                  {:else}
                    <button
                      class="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      onclick={(e) => { e.stopPropagation(); handlePullModel(model.id); }}
                      disabled={pullingModel}
                    >
                      {pullingModel && pullProgress?.includes(model.id) ? '下载中...' : '下载'}
                    </button>
                  {/if}
                </div>
              </button>
            {/each}
          </div>

          {#if pullProgress && !pullingModel}
            <div class="mt-4 p-3 bg-green-50 text-green-800 rounded-lg text-sm">
              {pullProgress}
            </div>
          {/if}

          <div class="flex justify-between mt-8">
            <button class="btn-secondary" onclick={prevStep}>← 返回</button>
            <button
              class="btn-primary"
              onclick={nextStep}
              disabled={!onboardingState.selectedModel}
            >
              下一步 →
            </button>
          </div>
        </div>

      {:else if onboardingState.currentStep === 3}
        <!-- Step 3: Import Data -->
        <div class="py-4">
          <h2 class="text-2xl font-bold text-gray-800 mb-2">导入对话数据</h2>
          <p class="text-gray-600 mb-6">现在导入一些对话数据来体验功能</p>

          <div class="max-w-md mx-auto text-center">
            <div class="text-6xl mb-4">📁</div>
            <p class="text-gray-600 mb-6">
              您可以现在导入对话文件，或者稍后在应用中导入
            </p>

            <div class="space-y-3">
              <button
                class="w-full btn-primary"
                onclick={() => { markDataImported(); nextStep(); }}
              >
                现在导入
              </button>
              <button
                class="w-full btn-secondary"
                onclick={() => { markDataImported(); nextStep(); }}
              >
                稍后再说
              </button>
            </div>
          </div>

          <div class="flex justify-between mt-8">
            <button class="btn-secondary" onclick={prevStep}>← 返回</button>
          </div>
        </div>

      {:else if onboardingState.currentStep === 4}
        <!-- Step 4: Complete -->
        <div class="text-center py-8">
          <div class="text-6xl mb-6">✨</div>
          <h2 class="text-3xl font-bold text-gray-800 mb-4">设置完成！</h2>
          <p class="text-gray-600 mb-8">
            准备好了吗？让我们开始使用 Mem-Switch
          </p>

          <div class="grid grid-cols-2 gap-4 max-w-md mx-auto mb-8">
            <div class="p-4 bg-blue-50 rounded-xl">
              <div class="text-2xl mb-2">🎯</div>
              <div class="font-medium">搜索记忆</div>
            </div>
            <div class="p-4 bg-green-50 rounded-xl">
              <div class="text-2xl mb-2">📊</div>
              <div class="font-medium">查看统计</div>
            </div>
          </div>

          <button class="btn-primary px-12 py-3 text-lg" onclick={handleComplete}>
            开始使用 🚀
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>
