<script>
  import { appState } from '../stores/app.svelte.js';
  import { hardwareState } from '../stores/hardware.svelte.js';
</script>

<footer class="h-8 bg-white border-t border-gray-200 flex items-center px-4 text-sm text-gray-500">
  <span class="flex items-center gap-2">
    <span class="w-2 h-2 rounded-full {appState.backendReady ? 'bg-green-500' : 'bg-red-500'}"></span>
    后端: {appState.backendReady ? '已连接' : '未连接'}
  </span>
  <span class="mx-4">|</span>
  <span class="flex items-center gap-2">
    <span class="w-2 h-2 rounded-full {hardwareState.ollamaConnected ? 'bg-green-500' : 'bg-gray-300'}"></span>
    Ollama: {hardwareState.ollamaConnected ? hardwareState.selectedModel || '已连接' : '未连接'}
  </span>
</footer>
