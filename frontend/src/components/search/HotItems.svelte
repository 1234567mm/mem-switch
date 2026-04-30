<script>
  let { items = { memory: [], knowledge: [] } } = $props();
</script>

<div class="space-y-4">
  {#if items.memory && items.memory.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-2">🔥 热门记忆</h4>
      <div class="space-y-1">
        {#each items.memory as item}
          <div class="px-3 py-2 text-sm text-gray-700 flex justify-between items-center bg-orange-50 rounded">
            <span class="truncate flex-1">{item.content}</span>
            <span class="text-xs text-orange-600 ml-2">{item.call_count}次</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if items.knowledge && items.knowledge.length > 0}
    <div>
      <h4 class="text-sm font-medium text-gray-500 mb-2">📖 热门知识</h4>
      <div class="space-y-1">
        {#each items.knowledge as item}
          <div class="px-3 py-2 text-sm text-gray-700 flex justify-between items-center bg-blue-50 rounded">
            <span class="truncate flex-1">{item.title}</span>
            <span class="text-xs text-blue-600 ml-2">{item.view_count}次</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>