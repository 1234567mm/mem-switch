<script>
  import { appState } from '../stores/app.svelte.js';
  const tabs = [
    { id: 'startup', label: '启动引导', icon: '⚡' },
    { id: 'knowledge', label: '知识库', icon: '📚' },
    { id: 'memory', label: '记忆库', icon: '🧠' },
    { id: 'import', label: '对话导入', icon: '📥' },
    { id: 'channel', label: '通道路由', icon: '🔀' },
    { id: 'settings', label: '设置', icon: '⚙️' },
  ];
</script>

<nav class="w-56 h-full bg-gray-900 text-white flex flex-col">
  <div class="p-4 text-xl font-bold border-b border-gray-700">Mem-Switch</div>
  <ul class="flex-1 py-2">
    {#each tabs as tab}
      <li>
        <button
          class="w-full px-4 py-3 text-left hover:bg-gray-800 {appState.currentTab === tab.id ? 'bg-gray-800 text-blue-400' : ''}"
          onclick={() => appState.currentTab = tab.id}
        >
          {tab.icon} {tab.label}
        </button>
      </li>
    {/each}
  </ul>
</nav>
