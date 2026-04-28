<script>
  import { appState } from './stores/app.svelte.js';
  import Sidebar from './components/Sidebar.svelte';
  import StatusBar from './components/StatusBar.svelte';

  let placeholderLabel = $derived(
    appState.currentTab === 'knowledge' ? '知识库' :
    appState.currentTab === 'memory' ? '记忆库' :
    appState.currentTab === 'import' ? '对话导入' : ''
  );
</script>

<div class="flex h-screen bg-gray-100">
  <Sidebar />
  <main class="flex-1 flex flex-col">
    <div class="flex-1 overflow-auto">
      {#if appState.currentTab === 'startup'}
        <div class="flex items-center justify-center h-full text-gray-500">
          启动引导 - 组件开发中
        </div>
      {:else if appState.currentTab === 'settings'}
        <div class="flex items-center justify-center h-full text-gray-500">
          设置 - 组件开发中
        </div>
      {:else}
        <div class="flex items-center justify-center h-full text-gray-500 text-xl">
          {placeholderLabel} - Phase 2 开发中
        </div>
      {/if}
    </div>
    <StatusBar />
  </main>
</div>
