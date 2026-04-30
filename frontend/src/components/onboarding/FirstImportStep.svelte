<script>
  let { onPrev, onComplete, onImportNow, onSkip } = $props();
</script>

<div class="py-4">
  <h2 class="text-2xl font-bold text-gray-800 mb-2">导入对话数据</h2>
  <p class="text-gray-600 mb-6">现在导入一些对话数据来体验功能</p>

  <div class="max-w-md mx-auto text-center">
    <div class="text-6xl mb-4">📁</div>
    <p class="text-gray-600 mb-6">
      您可以现在导入对话文件，或者稍后在应用中导入
    </p>

    <div class="space-y-3">
      <button
        class="w-full btn-primary"
        onclick={() => { onImportNow(); onComplete(); }}
      >
        现在导入
      </button>
      <button
        class="w-full btn-secondary"
        onclick={onSkip}
      >
        稍后再说
      </button>
    </div>
  </div>

  <div class="flex justify-between mt-8">
    <button class="btn-secondary" onclick={onPrev}>← 返回</button>
  </div>
</div>