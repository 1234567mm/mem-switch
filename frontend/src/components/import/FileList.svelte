<script>
  let { files = [], onRemove } = $props();

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
</script>

<div class="border rounded-lg divide-y">
  {#each files as file, i}
    <div class="flex items-center justify-between p-3">
      <div class="flex items-center gap-3">
        <span class="text-lg">📄</span>
        <div>
          <div class="font-medium text-gray-800">{file.name}</div>
          <div class="text-xs text-gray-500">{formatSize(file.size)}</div>
        </div>
      </div>
      <button
        class="text-gray-400 hover:text-red-500 text-xl leading-none"
        onclick={() => onRemove(i)}
        title="移除文件"
      >
        ×
      </button>
    </div>
  {/each}
</div>
