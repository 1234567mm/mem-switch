<script>
  let { items = [], onSelect } = $props();

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

{#if items.length > 0}
<div>
  <div class="flex items-center justify-between mb-3">
    <h4 class="text-sm font-medium text-gray-500">搜索历史</h4>
    <button class="text-xs text-blue-500 hover:underline">清除</button>
  </div>
  <div class="space-y-1">
    {#each items as item}
      <button
        class="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg flex justify-between items-center"
        onclick={() => onSelect(item.query)}
      >
        <span>🔍 {item.query}</span>
        <span class="text-xs text-gray-400">{formatTime(item.timestamp)}</span>
      </button>
    {/each}
  </div>
</div>
{/if}