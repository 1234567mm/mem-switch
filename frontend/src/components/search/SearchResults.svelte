<script>
  let { results } = $props();

  function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const hours = diff / (1000 * 60 * 60);
    if (hours < 1) return '刚刚';
    if (hours < 24) return `${Math.floor(hours)}小时前`;
    const days = hours / 24;
    if (days < 7) return `${Math.floor(days)}天前`;
    return date.toLocaleDateString();
  }
</script>

<div class="space-y-6">
  {#if results.memory && results.memory.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
        🧠 记忆库 ({results.memory.length})
      </h4>
      <div class="space-y-2">
        {#each results.memory as item}
          <div class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <div class="flex justify-between items-start mb-1">
              <span class="badge badge-info">{item.memory_type}</span>
              <span class="text-xs text-gray-400">{formatTime(item.created_at)}</span>
            </div>
            <p class="text-sm text-gray-700 line-clamp-2">{item.content}</p>
            {#if item.call_count > 0}
              <div class="text-xs text-gray-400 mt-1">调用 {item.call_count} 次</div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if results.knowledge && results.knowledge.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
        📚 知识库 ({results.knowledge.length})
      </h4>
      <div class="space-y-2">
        {#each results.knowledge as item}
          <div class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <div class="flex justify-between items-start mb-1">
              <span class="font-medium text-gray-800">{item.title}</span>
              <span class="text-xs text-gray-400">{formatTime(item.created_at)}</span>
            </div>
            <p class="text-sm text-gray-600">{item.kb_name}</p>
            <p class="text-xs text-gray-400 mt-1 line-clamp-1">{item.content}</p>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>