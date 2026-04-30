<script>
  import { appState } from './stores/app.svelte.js';
  import { toastState, addToast } from './stores/toast.svelte.js';
  import Sidebar from './components/Sidebar.svelte';
  import StatusBar from './components/StatusBar.svelte';
  import StartupGuide from './components/StartupGuide.svelte';
  import SettingsView from './components/SettingsView.svelte';
  import ImportView from './components/ImportView.svelte';
  import ChannelManagerView from './components/ChannelManagerView.svelte';
  import KnowledgeView from './components/KnowledgeView.svelte';
  import MemoryView from './components/MemoryView.svelte';
  import Toast from './components/shared/Toast.svelte';

  let placeholderLabel = $derived(
    appState.currentTab === 'knowledge' ? '知识库' :
    appState.currentTab === 'memory' ? '记忆库' :
    appState.currentTab === 'import' ? '对话导入' :
    appState.currentTab === 'channel' ? '通道路由' : ''
  );

  // 监听后端连接状态
  $effect(() => {
    const checkBackend = async () => {
      try {
        await fetch(appState.backendUrl + '/api/health');
        if (!appState.backendReady) {
          appState.backendReady = true;
          addToast('后端服务已连接', 'success');
        }
      } catch {
        if (appState.backendReady) {
          appState.backendReady = false;
          addToast('后端服务连接断开', 'error');
        }
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 3000);
    return () => clearInterval(interval);
  });
</script>

<div class="flex h-screen bg-gray-50">
  <Sidebar />
  <main class="flex-1 flex flex-col relative">
    <div class="flex-1 overflow-auto">
      {#if appState.currentTab === 'startup'}
        <StartupGuide />
      {:else if appState.currentTab === 'settings'}
        <SettingsView />
      {:else if appState.currentTab === 'import'}
        <ImportView />
      {:else if appState.currentTab === 'channel'}
        <ChannelManagerView />
      {:else if appState.currentTab === 'knowledge'}
        <KnowledgeView />
      {:else if appState.currentTab === 'memory'}
        <MemoryView />
      {:else}
        <div class="flex items-center justify-center h-full text-gray-500 text-xl">
          {placeholderLabel} - Phase 2 开发中
        </div>
      {/if}
    </div>
    <StatusBar />
  </main>
</div>

<!-- Toast 通知层 -->
<div class="fixed top-4 right-4 z-50 flex flex-col gap-2">
  {#each toastState.toasts as toast (toast.id)}
    <Toast {...toast} />
  {/each}
</div>