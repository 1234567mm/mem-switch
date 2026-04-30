<script>
  let { scopes, onToggle } = $props();
  const scopeLabels = { memory: '记忆', knowledge: '知识' };
</script>

<div class="flex gap-4">
  {#each Object.entries(scopeLabels) as [key, label]}
    <label class="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={scopes[key]}
        onchange={() => onToggle(key)}
        class="w-4 h-4 rounded border-gray-300 text-blue-500"
      />
      <span class="text-sm text-gray-700">{label}</span>
    </label>
  {/each}
</div>
