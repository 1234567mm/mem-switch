<script>
  import { appState } from '../stores/app.svelte.js';
  import { toggleSearch } from '../stores/search.svelte.js';

  const tabs = [
    { id: 'startup', label: '启动引导', icon: '⚡' },
    { id: 'knowledge', label: '知识库', icon: '📚' },
    { id: 'memory', label: '记忆库', icon: '🧠' },
    { id: 'import', label: '对话导入', icon: '📥' },
    { id: 'channel', label: '通道路由', icon: '🔀' },
    { id: 'settings', label: '设置', icon: '⚙️' },
  ];
</script>

<nav class="w-56 h-full bg-white border-r border-gray-200 flex flex-col shadow-sm">
  <div class="p-4 text-xl font-bold text-gray-800 border-b border-gray-100">
    <span class="text-blue-500">Mem</span>-Switch
  </div>
  <div class="p-3 border-b border-gray-100">
    <button
      class="w-full flex items-center gap-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
      onclick={toggleSearch}
    >
      <span>🔍</span>
      <span class="text-sm">搜索</span>
    </button>
  </div>
  <ul class="flex-1 py-2">
    {#each tabs as tab}
      <li>
        <button
          class="w-full px-4 py-3 text-left flex items-center gap-3 transition-colors {appState.currentTab === tab.id ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-500' : 'text-gray-600 hover:bg-gray-50'}"
          onclick={() => appState.currentTab = tab.id}
        >
          <span>{tab.icon}</span>
          <span class="font-medium">{tab.label}</span>
        </button>
      </li>
    {/each}
  </ul>
  <div class="p-4 border-t border-gray-100 text-xs text-gray-400">
    v0.1.0 · Phase 2
  </div>
</nav>
