<script>
  let { status = 'extracting', memoriesExtracted = 0, currentStep = '' } = $props();

  const steps = [
    { id: 'parsing', label: '解析对话', icon: '📝' },
    { id: 'extracting', label: '提取记忆', icon: '🧠' },
    { id: 'saving', label: '保存结果', icon: '💾' },
  ];

  let currentIndex = $derived(
    status === 'parsing' ? 0 :
    status === 'extracting' ? 1 :
    status === 'saving' ? 2 : 3
  );
</script>

<div class="card p-6">
  <h3 class="font-semibold text-gray-800 mb-4">导入进度</h3>

  <div class="space-y-4">
    {#each steps as step, i}
      <div class="flex items-center gap-4">
        <div class="w-10 h-10 rounded-full flex items-center justify-center text-xl
          {i < currentIndex ? 'bg-green-100 text-green-600' :
           i === currentIndex ? 'bg-blue-100 text-blue-600 animate-pulse' :
           'bg-gray-100 text-gray-400'}">
          {#if i < currentIndex}
            ✓
          {:else}
            {step.icon}
          {/if}
        </div>
        <div class="flex-1">
          <div class="font-medium {i <= currentIndex ? 'text-gray-800' : 'text-gray-400'}">
            {step.label}
          </div>
          {#if i === currentIndex && currentStep}
            <div class="text-sm text-blue-600">{currentStep}</div>
          {/if}
        </div>
      </div>
    {/each}
  </div>

  {#if status === 'extracting' && memoriesExtracted > 0}
    <div class="mt-6 p-4 bg-blue-50 rounded-lg">
      <div class="text-sm text-blue-600 mb-1">已提取记忆</div>
      <div class="text-2xl font-bold text-blue-700">{memoriesExtracted}</div>
    </div>
  {/if}
</div>
