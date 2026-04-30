<script>
  import { appState } from '../../stores/app.svelte.js';
  import { addToast } from '../../stores/toast.svelte.js';
  import { api } from '../../lib/api.js';
  import DragDropZone from './DragDropZone.svelte';
  import ImportProgress from './ImportProgress.svelte';
  import ImportResultSummary from './ImportResultSummary.svelte';

  let { onComplete } = $props();

  // Wizard steps: source -> file -> preview -> importing -> result
  let currentStep = $state('source');
  let sourceType = $state('claude_code');
  let selectedFile = $state(null);
  let previewData = $state([]);
  let importResults = $state([]);
  let loading = $state(false);
  let importing = $state(false);
  let importStatus = $state('parsing');
  let memoriesExtracted = $state(0);
  let error = $state('');

  const sourceTypes = [
    { id: 'claude_code', label: 'Claude Code', icon: '🤖' },
    { id: 'codex', label: 'Codex', icon: '⚡' },
    { id: 'openclaw', label: 'OpenClaw', icon: '↯' },
    { id: 'opencode', label: 'OpenCode', icon: '⊕' },
    { id: 'gemini_cli', label: 'Gemini CLI', icon: '✦' },
    { id: 'hermes', label: 'Hermes', icon: '☿' },
    { id: 'json_file', label: 'JSON 文件', icon: '📄' },
    { id: 'markdown', label: 'Markdown', icon: '📝' },
    { id: 'clipboard', label: '剪贴板', icon: '📋' },
  ];

  function selectSource(type) {
    sourceType = type;
    currentStep = 'file';
  }

  function handleFileSelect(file) {
    selectedFile = file;
    currentStep = 'preview';
    loadPreview();
  }

  async function loadPreview() {
    loading = true;
    error = '';
    try {
      const resp = await api.import.preview(sourceType);
      previewData = resp.data || [];
    } catch (e) {
      error = '预览加载失败';
      addToast('预览加载失败', 'error');
    }
    loading = false;
  }

  async function startImport() {
    importing = true;
    importStatus = 'parsing';
    memoriesExtracted = 0;
    currentStep = 'importing';
    error = '';

    try {
      let resp;

      if (selectedFile) {
        // Upload file
        importStatus = 'saving';
        const formData = new FormData();
        formData.append('file', selectedFile);
        resp = await api.import.uploadFile(sourceType, formData);
      } else {
        // Import from source
        importStatus = 'extracting';
        resp = await api.import.conversations(sourceType);
      }

      importResults = Array.isArray(resp.data) ? resp.data : [resp.data];

      const successCount = importResults.filter(r => r.status === 'success').length;
      memoriesExtracted = importResults.reduce((sum, r) => sum + (r.memories_created || 0), 0);

      addToast(`导入完成！成功 ${successCount} 个会话，提取 ${memoriesExtracted} 条记忆`, 'success');
      currentStep = 'result';
    } catch (e) {
      error = e.message || '导入失败';
      addToast('导入失败: ' + error, 'error');
      currentStep = 'result';
    }

    importing = false;
  }

  function resetWizard() {
    currentStep = 'source';
    selectedFile = null;
    previewData = [];
    importResults = [];
    importStatus = 'parsing';
    memoriesExtracted = 0;
    error = '';
  }

  function goToMemories() {
    appState.currentTab = 'memory';
    if (onComplete) onComplete();
  }
</script>

<div class="max-w-4xl mx-auto p-8">
  <!-- Header -->
  <div class="text-center mb-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-2">对话导入</h1>
    <p class="text-gray-500">将 AI 对话记录导入为可管理的记忆</p>
  </div>

  <!-- Step Indicator -->
  <div class="flex justify-center mb-8">
    <div class="flex items-center gap-4">
      {#each ['来源', '文件', '预览', '导入'] as step, i}
        {@const stepKey = step === '来源' ? 'source' : step === '文件' ? 'file' : step === '预览' ? 'preview' : 'importing'}
        {@const isActive = currentStep === stepKey}
        {@const isComplete = ['source', 'file', 'preview', 'importing', 'result'].indexOf(currentStep) > i}
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
            {isComplete ? 'bg-green-500 text-white' : isActive ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'}">
            {#if isComplete}
              ✓
            {:else}
              {i + 1}
            {/if}
          </div>
          <span class="text-sm {isActive || isComplete ? 'text-gray-800 font-medium' : 'text-gray-400'}">
            {step}
          </span>
        </div>
        {#if i < 3}
          <div class="w-12 h-0.5 {isComplete ? 'bg-green-500' : 'bg-gray-200'}"></div>
        {/if}
      {/each}
    </div>
  </div>

  <!-- Step Content -->
  <div class="card p-8">
    {#if currentStep === 'source'}
      <!-- Step 1: Select Source -->
      <h2 class="text-xl font-semibold text-gray-800 mb-6 text-center">选择数据来源</h2>
      <div class="grid grid-cols-3 gap-4">
        {#each sourceTypes as src}
          <button
            class="p-4 border rounded-xl text-center hover:border-blue-500 hover:bg-blue-50 transition-all"
            onclick={() => selectSource(src.id)}
          >
            <div class="text-3xl mb-2">{src.icon}</div>
            <div class="font-medium text-gray-800">{src.label}</div>
          </button>
        {/each}
      </div>

    {:else if currentStep === 'file'}
      <!-- Step 2: Select File -->
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <button class="text-blue-600 hover:underline" onclick={() => currentStep = 'source'}>
            ← 返回选择来源
          </button>
          <span class="text-gray-400">|</span>
          <span class="text-gray-600">
            已选择: {sourceTypes.find(s => s.id === sourceType)?.label}
          </span>
        </div>
      </div>

      <h2 class="text-xl font-semibold text-gray-800 mb-6 text-center">上传对话文件</h2>

      <DragDropZone onFileSelect={handleFileSelect} />

      <div class="mt-6 text-center">
        <button
          class="text-blue-600 hover:underline"
          onclick={() => { selectedFile = null; currentStep = 'preview'; loadPreview(); }}
        >
          或从已有数据源导入（不上传文件）
        </button>
      </div>

    {:else if currentStep === 'preview'}
      <!-- Step 3: Preview -->
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <button class="text-blue-600 hover:underline" onclick={() => currentStep = 'file'}>
            ← 返回上传文件
          </button>
        </div>
      </div>

      <h2 class="text-xl font-semibold text-gray-800 mb-6 text-center">预览对话数据</h2>

      {#if loading}
        <div class="text-center py-12 text-gray-500">加载中...</div>
      {:else if previewData.length === 0}
        <div class="text-center py-12">
          <div class="text-gray-400 mb-4">未检测到对话数据</div>
          <button class="btn-secondary" onclick={loadPreview}>
            重新扫描
          </button>
        </div>
      {:else}
        <div class="space-y-3 mb-6">
          {#each previewData.slice(0, 5) as item}
            <div class="p-4 border rounded-lg bg-gray-50">
              <div class="flex justify-between mb-1">
                <span class="font-medium text-gray-800">{item.source || sourceType}</span>
                <span class="text-sm text-gray-500">{item.message_count || 0} 条消息</span>
              </div>
              {#if item.preview}
                <p class="text-sm text-gray-500 truncate">{item.preview}</p>
              {/if}
            </div>
          {/each}
          {#if previewData.length > 5}
            <div class="text-center text-gray-400 text-sm">
              还有 {previewData.length - 5} 个会话...
            </div>
          {/if}
        </div>

        <div class="flex justify-center gap-4">
          <button class="btn-secondary" onclick={loadPreview}>
            重新扫描
          </button>
          <button
            class="btn-primary px-8"
            onclick={startImport}
          >
            开始导入 {previewData.length} 个会话
          </button>
        </div>
      {/if}

    {:else if currentStep === 'importing'}
      <!-- Step 4: Importing -->
      <ImportProgress
        status={importStatus}
        memoriesExtracted={memoriesExtracted}
        currentStep={importStatus === 'parsing' ? '正在解析对话内容...' : importStatus === 'extracting' ? '正在提取记忆...' : '正在保存...'}
      />

    {:else if currentStep === 'result'}
      <!-- Step 5: Result -->
      <ImportResultSummary
        results={importResults}
        onViewMemories={goToMemories}
        onImportMore={resetWizard}
      />
    {/if}
  </div>
</div>
