<script>
  let { onFileSelect } = $props();

  let isDragging = $state(false);
  let fileInput = $state(null);

  function handleDragOver(e) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave() {
    isDragging = false;
  }

  function handleDrop(e) {
    e.preventDefault();
    isDragging = false;
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  }

  function handleFileInput(e) {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  }

  function openFilePicker() {
    fileInput?.click();
  }
</script>

<div
  class="border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer {isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}"
  role="button"
  tabindex="0"
  ondragover={handleDragOver}
  ondragleave={handleDragLeave}
  ondrop={handleDrop}
  onclick={openFilePicker}
  onkeydown={(e) => e.key === 'Enter' && openFilePicker()}
>
  <input
    bind:this={fileInput}
    type="file"
    class="hidden"
    onchange={handleFileInput}
    accept=".json,.md,.txt,.html"
  />

  <div class="text-5xl mb-4 {isDragging ? 'text-blue-500' : 'text-gray-400'}">
    📁
  </div>

  <div class="text-lg font-medium text-gray-700 mb-2">
    {#if isDragging}
      释放文件以上传
    {:else}
      拖拽文件到此处
    {/if}
  </div>

  <div class="text-sm text-gray-500 mb-4">
    或点击选择文件
  </div>

  <div class="text-xs text-gray-400">
    支持格式: JSON, Markdown, TXT, HTML
  </div>
</div>
