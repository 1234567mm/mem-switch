<script>
  let { total, completed, failed, skipped, currentFile } = $props();

  $ progressPercent = total > 0 ? ((completed + failed + skipped) / total) * 100 : 0;
</script>

<div class="space-y-4">
  <!-- 总体进度条 -->
  <div>
    <div class="flex justify-between text-sm mb-2">
      <span class="font-medium text-gray-700">进度</span>
      <span class="text-gray-600">{completed + failed + skipped} / {total}</span>
    </div>
    <div class="h-3 bg-gray-200 rounded-full overflow-hidden">
      <div
        class="h-full bg-blue-500 transition-all duration-300"
        style="width: {progressPercent}%"
      />
    </div>
  </div>

  <!-- 状态统计 -->
  <div class="flex gap-4 text-sm">
    <span class="text-green-600 font-medium">✓ 完成 {completed}</span>
    <span class="text-amber-600 font-medium">⊘ 跳过 {skipped}</span>
    <span class="text-red-600 font-medium">✗ 失败 {failed}</span>
  </div>

  <!-- 当前处理文件 -->
  {#if currentFile && (completed + failed + skipped) < total}
    <div class="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
      <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <span class="text-sm text-gray-700">正在处理：<span class="font-medium">{currentFile}</span></span>
    </div>
  {/if}
</div>
