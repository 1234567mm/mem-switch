<script>
  let { results = [], onViewMemories, onImportMore } = $props();

  let successCount = $derived(results.filter(r => r.status === 'success').length);
  let failCount = $derived(results.filter(r => r.status === 'error').length);
  let totalMemories = $derived(results.reduce((sum, r) => sum + (r.memories_created || 0), 0));
  let totalMessages = $derived(results.reduce((sum, r) => sum + (r.messages_count || 0), 0));
</script>

<div class="space-y-6">
  <!-- Summary Stats -->
  <div class="card p-6">
    <h3 class="font-semibold text-gray-800 mb-4">导入结果摘要</h3>

    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="text-center p-4 bg-green-50 rounded-lg">
        <div class="text-3xl font-bold text-green-600">{successCount}</div>
        <div class="text-sm text-gray-600">成功</div>
      </div>
      {#if failCount > 0}
        <div class="text-center p-4 bg-red-50 rounded-lg">
          <div class="text-3xl font-bold text-red-600">{failCount}</div>
          <div class="text-sm text-gray-600">失败</div>
        </div>
      {/if}
      <div class="text-center p-4 bg-blue-50 rounded-lg">
        <div class="text-3xl font-bold text-blue-600">{totalMemories}</div>
        <div class="text-sm text-gray-600">记忆</div>
      </div>
      <div class="text-center p-4 bg-purple-50 rounded-lg">
        <div class="text-3xl font-bold text-purple-600">{totalMessages}</div>
        <div class="text-sm text-gray-600">消息</div>
      </div>
    </div>

    <div class="flex gap-3">
      {#if onViewMemories}
        <button class="btn-primary" onclick={onViewMemories}>
          查看记忆库 →
        </button>
      {/if}
      {#if onImportMore}
        <button class="btn-secondary" onclick={onImportMore}>
          继续导入
        </button>
      {/if}
    </div>
  </div>

  <!-- Individual Results -->
  {#if results.length > 0}
    <div class="card p-6">
      <h4 class="font-medium text-gray-700 mb-4">导入详情</h4>
      <div class="space-y-3">
        {#each results as result}
          <div class="flex items-center gap-4 p-3 rounded-lg {result.status === 'success' ? 'bg-green-50' : 'bg-red-50'}">
            <span class="text-xl">
              {result.status === 'success' ? '✓' : '✗'}
            </span>
            <div class="flex-1">
              <div class="font-medium text-gray-800">
                {result.session_id || result.source || '会话'}
              </div>
              {#if result.status === 'error'}
                <div class="text-sm text-red-600">{result.error}</div>
              {:else}
                <div class="text-sm text-gray-500">
                  {result.messages_count || 0} 条消息 · {result.memories_created || 0} 条记忆
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
