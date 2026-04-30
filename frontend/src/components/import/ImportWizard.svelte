<script>
  import { appState } from '../../stores/app.svelte.js';
  import { addToast } from '../../stores/toast.svelte.js';
  import { api } from '../../lib/api.js';
  import DragDropZone from './DragDropZone.svelte';
  import FileList from './FileList.svelte';
  import BatchProgress from './BatchProgress.svelte';

  let { onComplete } = $props();

  // Wizard steps: source -> file -> preview -> importing -> result
  let currentStep = $state('source');
  let sourceType = $state('claude_code');
  let selectedFiles = $state([]);
  let currentTask = $state(null);
  let importing = $state(false);
  let progress = $state({ total: 0, completed: 0, failed: 0, skipped: 0 });
  let currentFile = $state('');
  let importResults = $state([]);
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

  function handleFilesSelect(files) {
    if (Array.isArray(files)) {
      selectedFiles = [...selectedFiles, ...files];
    } else {
      selectedFiles = [...selectedFiles, files];
    }
  }

  function removeFile(index) {
    selectedFiles = selectedFiles.filter((_, i) => i !== index);
  }

  function clearFiles() {
    selectedFiles = [];
  }

  function goToPreview() {
    if (selectedFiles.length === 0) {
      addToast('请至少选择一个文件', 'error');
      return;
    }
    currentStep = 'preview';
  }

  async function startBatchImport() {
    importing = true;
    currentStep = 'importing';
    currentTask = null;
    progress = { total: selectedFiles.length, completed: 0, failed: 0, skipped: 0 };
    error = '';

    try {
      // 调用批量导入 API
      const resp = await api.import.batch(sourceType, selectedFiles.map(f => f.path || f.name));
      currentTask = resp.data.task_id;

      addToast(`批量导入已开始，共 ${selectedFiles.length} 个文件`, 'success');

      // 轮询任务状态
      pollTaskStatus(currentTask);
    } catch (e) {
      error = e.message || '导入失败';
      addToast('导入失败：' + error, 'error');
      importing = false;
      currentStep = 'result';
    }
  }

  async function pollTaskStatus(taskId) {
    while (importing) {
      try {
        const resp = await api.import.getTaskStatus(taskId);
        const data = resp.data;

        progress = {
          total: data.total_files,
          completed: data.completed_files,
          failed: data.failed_files,
          skipped: data.skipped_files
        };

        // 更新当前处理文件
        if (data.files && data.files.length > 0) {
          const processingFile = data.files.find(f => f.status === 'processing');
          currentFile = processingFile?.file_name || '';
        }

        if (data.status === 'completed' || data.status === 'failed') {
          importing = false;

          if (data.status === 'completed') {
            addToast(
              `导入完成：${data.completed_files} 成功，${data.skipped_files} 跳过，${data.failed_files} 失败`,
              'success'
            );
          } else {
            addToast(
              `导入完成（部分失败）：${data.completed_files} 成功，${data.skipped_files} 跳过，${data.failed_files} 失败`,
              'warning'
            );
          }

          importResults = data.files || [];
          currentStep = 'result';
          break;
        }
      } catch (e) {
        error = e.message || '轮询状态失败';
        addToast('轮询状态失败', 'error');
        importing = false;
        currentStep = 'result';
        break;
      }

      // 每 2 秒轮询一次
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  function resetWizard() {
    currentStep = 'source';
    selectedFiles = [];
    currentTask = null;
    importing = false;
    progress = { total: 0, completed: 0, failed: 0, skipped: 0 };
    currentFile = '';
    importResults = [];
    error = '';
  }

  function goToMemories() {
    appState.currentTab = 'memory';
    if (onComplete) onComplete();
  }

  function hasSelectedFiles() {
    return selectedFiles.length > 0;
  }
</script>

<div class="max-w-4xl mx-auto p-8">
  <!-- Header -->
  <div class="text-center mb-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-2">批量导入对话</h1>
    <p class="text-gray-500">将多个 AI 对话记录批量导入为可管理的记忆</p>
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
      <!-- Step 2: Select Files -->
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <button class="text-blue-600 hover:underline" onclick={() => currentStep = 'source'}>
            ← 返回选择来源
          </button>
          <span class="text-gray-400">|</span>
          <span class="text-gray-600">
            已选择：{sourceTypes.find(s => s.id === sourceType)?.label}
          </span>
        </div>
      </div>

      <h2 class="text-xl font-semibold text-gray-800 mb-6 text-center">选择对话文件</h2>

      <DragDropZone multiple={true} onFilesSelect={handleFilesSelect} />

      {#if hasSelectedFiles()}
        <div class="mt-6">
          <FileList files={selectedFiles} onRemove={removeFile} />
        </div>
      {/if}

      <div class="flex justify-center gap-4 mt-6">
        <button
          class="btn-secondary"
          onclick={clearFiles}
          disabled={!hasSelectedFiles()}
        >
          清空文件
        </button>
        <button
          class="btn-primary px-8"
          onclick={goToPreview}
          disabled={!hasSelectedFiles()}
        >
          下一步：预览 {hasSelectedFiles() ? `(${selectedFiles.length} 个文件)` : ''}
        </button>
      </div>

    {:else if currentStep === 'preview'}
      <!-- Step 3: Preview -->
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <button class="text-blue-600 hover:underline" onclick={() => currentStep = 'file'}>
            ← 返回文件选择
          </button>
        </div>
      </div>

      <h2 class="text-xl font-semibold text-gray-800 mb-6 text-center">确认导入</h2>

      <div class="space-y-3 mb-6">
        <div class="p-4 bg-blue-50 rounded-lg">
          <div class="flex items-center gap-2 text-blue-800">
            <span class="text-xl">ℹ️</span>
            <span class="font-medium">导入说明</span>
          </div>
          <ul class="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
            <li>共选择 <strong>{selectedFiles.length}</strong> 个文件</li>
            <li>已导入的会话将自动跳过</li>
            <li>并发处理数限制为 2 个文件</li>
            <li>失败的文件可以重新尝试导入</li>
          </ul>
        </div>

        <div class="p-4 border rounded-lg bg-gray-50">
          <div class="text-sm font-medium text-gray-700 mb-2">文件列表</div>
          <div class="max-h-60 overflow-y-auto space-y-1">
            {#each selectedFiles as file, i}
              <div class="flex items-center gap-2 text-sm text-gray-600">
                <span class="text-gray-400">{i + 1}.</span>
                <span class="truncate">{file.name}</span>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <div class="flex justify-center gap-4">
        <button class="btn-secondary" onclick={() => currentStep = 'file'}>
          返回修改
        </button>
        <button
          class="btn-primary px-8"
          onclick={startBatchImport}
        >
          开始导入
        </button>
      </div>

    {:else if currentStep === 'importing'}
      <!-- Step 4: Importing -->
      <BatchProgress
        total={progress.total}
        completed={progress.completed}
        failed={progress.failed}
        skipped={progress.skipped}
        currentFile={currentFile}
      />

    {:else if currentStep === 'result'}
      <!-- Step 5: Result -->
      <div class="text-center">
        <div class="text-5xl mb-4">
          {#if progress.failed === 0}
            ✅
          {:else}
            ⚠️
          {/if}
        </div>

        <h2 class="text-xl font-semibold text-gray-800 mb-4">
          {#if progress.failed === 0}
            导入完成！
          {:else}
            导入完成（部分失败）
          {/if}
        </h2>

        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="p-4 bg-green-50 rounded-lg">
            <div class="text-2xl font-bold text-green-600">{progress.completed}</div>
            <div class="text-sm text-green-700">成功</div>
          </div>
          <div class="p-4 bg-amber-50 rounded-lg">
            <div class="text-2xl font-bold text-amber-600">{progress.skipped}</div>
            <div class="text-sm text-amber-700">跳过</div>
          </div>
          <div class="p-4 bg-red-50 rounded-lg">
            <div class="text-2xl font-bold text-red-600">{progress.failed}</div>
            <div class="text-sm text-red-700">失败</div>
          </div>
        </div>

        {#if importResults.length > 0 && importResults.some(f => f.status === 'failed')}
          <div class="mb-6 p-4 border rounded-lg bg-gray-50 text-left">
            <div class="font-medium text-gray-700 mb-2">失败文件详情</div>
            <div class="space-y-2 text-sm">
              {#each importResults.filter(f => f.status === 'failed') as file}
                <div class="flex items-start gap-2">
                  <span class="text-red-500">✗</span>
                  <div>
                    <div class="font-medium text-gray-800">{file.file_name}</div>
                    <div class="text-red-600">{file.error || '未知错误'}</div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <div class="flex justify-center gap-4">
          <button class="btn-secondary" onclick={resetWizard}>
            导入更多文件
          </button>
          <button class="btn-primary" onclick={goToMemories}>
            查看记忆
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
