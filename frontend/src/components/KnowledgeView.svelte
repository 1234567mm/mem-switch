<script>
  import { api } from '../lib/api.js';

  let knowledgeBases = $state([]);
  let selectedKb = $state(null);
  let documents = $state([]);
  let searchQuery = $state('');
  let searchResults = $state([]);
  let loading = $state(false);
  let error = $state('');
  let showCreateModal = $state(false);
  let newKbName = $state('');
  let newKbDesc = $state('');
  let uploading = $state(false);

  async function loadKnowledgeBases() {
    loading = true;
    error = '';
    try {
      const resp = await api.knowledge.listBases();
      knowledgeBases = resp.data;
    } catch (e) {
      error = '加载知识库失败: ' + e.message;
    }
    loading = false;
  }

  async function createKnowledgeBase() {
    if (!newKbName.trim()) return;
    try {
      await api.knowledge.createBase({ name: newKbName, description: newKbDesc });
      showCreateModal = false;
      newKbName = '';
      newKbDesc = '';
      await loadKnowledgeBases();
    } catch (e) {
      error = '创建知识库失败: ' + e.message;
    }
  }

  async function selectKnowledgeBase(kb) {
    selectedKb = kb;
    searchResults = [];
    searchQuery = '';
    try {
      const resp = await api.knowledge.listDocs(kb.kb_id);
      documents = resp.data;
    } catch (e) {
      documents = [];
    }
  }

  async function deleteKnowledgeBase(kb) {
    if (!confirm(`确定删除知识库 "${kb.name}" 吗？`)) return;
    try {
      await api.knowledge.deleteBase(kb.kb_id);
      if (selectedKb?.kb_id === kb.kb_id) {
        selectedKb = null;
        documents = [];
      }
      await loadKnowledgeBases();
    } catch (e) {
      error = '删除知识库失败: ' + e.message;
    }
  }

  async function handleFileUpload(event, kbId) {
    const file = event.target.files[0];
    if (!file) return;
    uploading = true;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await api.knowledge.uploadDoc(kbId, formData);
      const resp = await api.knowledge.listDocs(kbId);
      documents = resp.data;
    } catch (e) {
      error = '上传文档失败: ' + e.message;
    }
    uploading = false;
    event.target.value = '';
  }

  async function searchKnowledge() {
    if (!searchQuery.trim() || !selectedKb) return;
    loading = true;
    try {
      const resp = await api.knowledge.search(selectedKb.kb_id, searchQuery, 10);
      searchResults = resp.data;
    } catch (e) {
      error = '搜索失败: ' + e.message;
    }
    loading = false;
  }

  $effect(() => {
    loadKnowledgeBases();
  });
</script>

<div class="max-w-6xl mx-auto p-6">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">知识库</h1>
    <button
      class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      onclick={() => showCreateModal = true}
    >
      创建知识库
    </button>
  </div>

  {#if error}
    <div class="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>
  {/if}

  <div class="grid grid-cols-3 gap-6">
    <!-- 知识库列表 -->
    <div class="col-span-1 bg-white rounded-lg shadow p-4">
      <h2 class="font-semibold mb-3">知识库列表</h2>
      {#if loading && knowledgeBases.length === 0}
        <p class="text-gray-500">加载中...</p>
      {:else if knowledgeBases.length === 0}
        <p class="text-gray-500">暂无知识库</p>
      {:else}
        <div class="space-y-2">
          {#each knowledgeBases as kb}
            <div
              class="p-3 rounded-lg cursor-pointer transition {selectedKb?.kb_id === kb.kb_id ? 'bg-blue-100 border-blue-300' : 'bg-gray-50 hover:bg-gray-100'}"
              onclick={() => selectKnowledgeBase(kb)}
            >
              <div class="font-medium">{kb.name}</div>
              <div class="text-sm text-gray-500">{kb.description || '无描述'}</div>
              <div class="text-xs text-gray-400 mt-1">{kb.document_count} 个文档</div>
              <button
                class="mt-2 text-xs text-red-600 hover:text-red-800"
                onclick={(e) => { e.stopPropagation(); deleteKnowledgeBase(kb); }}
              >
                删除
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- 知识库详情 -->
    <div class="col-span-2 bg-white rounded-lg shadow p-4">
      {#if !selectedKb}
        <div class="flex items-center justify-center h-64 text-gray-400">
          选择一个知识库查看详情
        </div>
      {:else}
        <h2 class="font-semibold mb-4">{selectedKb.name}</h2>

        <!-- 上传文档 -->
        <div class="mb-4">
          <label class="block mb-2 text-sm font-medium">上传文档</label>
          <input
            type="file"
            class="w-full text-sm border rounded-lg p-2"
            accept=".txt,.md,.pdf,.docx"
            onchange={(e) => handleFileUpload(e, selectedKb.kb_id)}
            disabled={uploading}
          />
          {#if uploading}
            <p class="text-sm text-blue-600 mt-1">上传中...</p>
          {/if}
        </div>

        <!-- 文档列表 -->
        <div class="mb-6">
          <h3 class="font-medium mb-2">文档列表 ({documents.length})</h3>
          {#if documents.length === 0}
            <p class="text-gray-400 text-sm">暂无文档</p>
          {:else}
            <div class="space-y-2">
              {#each documents as doc}
                <div class="p-2 bg-gray-50 rounded text-sm">
                  <div class="font-medium">{doc.filename}</div>
                  <div class="text-gray-500 text-xs">{doc.chunks_count} 个文本块</div>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        <!-- 搜索 -->
        <div class="border-t pt-4">
          <h3 class="font-medium mb-2">知识检索</h3>
          <div class="flex gap-2">
            <input
              type="text"
              class="flex-1 border rounded-lg px-3 py-2"
              placeholder="输入搜索内容..."
              bind:value={searchQuery}
              onkeydown={(e) => e.key === 'Enter' && searchKnowledge()}
            />
            <button
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              onclick={searchKnowledge}
              disabled={loading}
            >
              {loading ? '搜索中...' : '搜索'}
            </button>
          </div>

          {#if searchResults.length > 0}
            <div class="mt-4 space-y-3">
              {#each searchResults as result}
                <div class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-sm text-gray-600 mb-1">{result.filename}</div>
                  <div class="text-sm">{result.content}</div>
                  <div class="text-xs text-gray-400 mt-1">相似度: {Math.round(result.score * 100)}%</div>
                </div>
              {/each}
            </div>
          {:else if searchQuery && !loading}
            <p class="mt-2 text-gray-400 text-sm">无搜索结果</p>
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- 创建知识库弹窗 -->
{#if showCreateModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-96">
      <h2 class="text-lg font-semibold mb-4">创建知识库</h2>
      <div class="mb-4">
        <label class="block mb-1 text-sm font-medium">名称</label>
        <input
          type="text"
          class="w-full border rounded-lg px-3 py-2"
          bind:value={newKbName}
          placeholder="知识库名称"
        />
      </div>
      <div class="mb-4">
        <label class="block mb-1 text-sm font-medium">描述</label>
        <textarea
          class="w-full border rounded-lg px-3 py-2"
          bind:value={newKbDesc}
          placeholder="可选描述"
          rows="3"
        ></textarea>
      </div>
      <div class="flex justify-end gap-2">
        <button
          class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          onclick={() => showCreateModal = false}
        >
          取消
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          onclick={createKnowledgeBase}
        >
          创建
        </button>
      </div>
    </div>
  </div>
{/if}
