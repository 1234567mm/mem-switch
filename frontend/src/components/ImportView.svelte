<script>
  import { appState } from '../stores/app.svelte.js';

  const sourceTypes = [
    { id: 'claude_code', label: 'Claude Code' },
    { id: 'codex', label: 'Codex' },
    { id: 'openclaw', label: 'OpenClaw' },
    { id: 'opencode', label: 'OpenCode' },
    { id: 'gemini_cli', label: 'Gemini CLI' },
    { id: 'hermes', label: 'Hermes' },
    { id: 'json_file', label: 'JSON 文件' },
    { id: 'markdown', label: 'Markdown 文件' },
    { id: 'clipboard', label: '剪贴板' },
  ];

  let sourceType = $state('claude_code');
  let previewData = $state([]);
  let importResults = $state([]);
  let loading = $state(false);
  let importing = $state(false);
  let error = $state('');

  const API_BASE = appState.backendUrl;

  async function loadPreview() {
    loading = true;
    error = '';
    try {
      const resp = await fetch(`${API_BASE}/api/import/preview?source_type=${sourceType}`);
      if (!resp.ok) throw new Error('Preview failed');
      previewData = await resp.json();
    } catch (e) {
      error = '预览加载失败: ' + e.message;
    }
    loading = false;
  }

  async function startImport() {
    importing = true;
    error = '';
    importResults = [];
    try {
      const resp = await fetch(`${API_BASE}/api/import/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: sourceType,
          extract_memories: true,
        }),
      });
      if (!resp.ok) throw new Error('Import failed');
      importResults = await resp.json();
    } catch (e) {
      error = '导入失败: ' + e.message;
    }
    importing = false;
  }

  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    importing = true;
    error = '';
    try {
      const resp = await fetch(`${API_BASE}/api/import/upload?source_type=${sourceType}`, {
        method: 'POST',
        body: formData,
      });
      if (!resp.ok) throw new Error('Upload failed');
      importResults = await resp.json();
    } catch (e) {
      error = '上传失败: ' + e.message;
    }
    importing = false;
  }
</script>

<div class="max-w-4xl mx-auto p-8">
  <h1 class="text-3xl font-bold mb-6">对话导入</h1>

  <!-- 数据源选择 -->
  <div class="mb-6">
    <label class="block font-medium mb-2">选择数据源</label>
    <select
      class="w-full p-2 border rounded-lg"
      bind:value={sourceType}
    >
      {#each sourceTypes as src}
        <option value={src.id}>{src.label}</option>
      {/each}
    </select>
  </div>

  <!-- 预览区域 -->
  <div class="mb-6">
    <h2 class="text-xl font-semibold mb-3">预览</h2>
    {#if loading}
      <p class="text-gray-500">加载中...</p>
    {:else if previewData.length === 0}
      <p class="text-gray-500">未检测到对话数据，点击"扫描数据源"按钮</p>
      <button
        class="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        onclick={loadPreview}
      >
        扫描数据源
      </button>
    {:else}
      <div class="space-y-2">
        {#each previewData as item}
          <div class="p-3 border rounded-lg bg-gray-50">
            <div class="flex justify-between">
              <span class="font-medium">{item.source} - {item.session_id}</span>
              <span class="text-gray-500">{item.message_count} 条消息</span>
            </div>
            <p class="text-sm text-gray-600 mt-1 truncate">{item.preview}</p>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- 操作按钮 -->
  <div class="flex gap-4 mb-6">
    <button
      class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
      disabled={importing || previewData.length === 0}
      onclick={startImport}
    >
      {importing ? '导入中...' : '开始导入'}
    </button>

    <label class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 cursor-pointer">
      上传文件
      <input type="file" class="hidden" onchange={handleFileUpload} />
    </label>
  </div>

  <!-- 错误提示 -->
  {#if error}
    <div class="mb-6 p-3 bg-red-100 border border-red-400 rounded-lg text-red-700">
      {error}
    </div>
  {/if}

  <!-- 导入结果 -->
  {#if importResults.length > 0}
    <div>
      <h2 class="text-xl font-semibold mb-3">导入结果</h2>
      <div class="space-y-2">
        {#each importResults as result}
          <div class="p-3 border rounded-lg {result.status === 'success' ? 'bg-green-50' : 'bg-red-50'}">
            <div class="flex justify-between">
              <span>{result.session_id || result.error}</span>
              <span class="{result.status === 'success' ? 'text-green-600' : 'text-red-600'}">
                {result.status}
              </span>
            </div>
            {#if result.status === 'success'}
              <p class="text-sm text-gray-600">
                消息: {result.messages_count} | 记忆: {result.memories_created}
              </p>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>