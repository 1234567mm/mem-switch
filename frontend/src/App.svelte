<script>
  import { appState } from './stores/app.svelte.js';
  import Sidebar from './components/Sidebar.svelte';
  import StatusBar from './components/StatusBar.svelte';
  import StartupGuide from './components/StartupGuide.svelte';
  import SettingsView from './components/SettingsView.svelte';
  import ImportView from './components/ImportView.svelte';

  let placeholderLabel = $derived(
    appState.currentTab === 'knowledge' ? '知识库' :
    appState.currentTab === 'memory' ? '记忆库' :
    appState.currentTab === 'import' ? '对话导入' : ''
  );

  // 监听后端连接状态
  $effect(() => {
    const checkBackend = async () => {
      try {
        await fetch(appState.backendUrl + '/api/health');
        appState.backendReady = true;
      } catch {
        appState.backendReady = false;
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 3000);
    return () => clearInterval(interval);
  });
</script>

<div class="flex h-screen bg-gray-100">
  <Sidebar />
  <main class="flex-1 flex flex-col">
    <div class="flex-1 overflow-auto">
      {#if appState.currentTab === 'startup'}
        <StartupGuide />
      {:else if appState.currentTab === 'settings'}
        <SettingsView />
      {:else if appState.currentTab === 'import'}
        <ImportView />
      {:else}
        <div class="flex items-center justify-center h-full text-gray-500 text-xl">
          {placeholderLabel} - Phase 2 开发中
        </div>
      {/if}
    </div>
    <StatusBar />
  </main>
</div>