<script>
  let { query = '', onInput } = $props();
</script>

<div class="relative">
  <input
    type="text"
    class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    placeholder="搜索记忆、知识..."
    value={query}
    oninput={(e) => onInput(e.target.value)}
  />
  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
</div>
