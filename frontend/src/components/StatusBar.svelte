<script>
  import { appState } from '../stores/app.svelte.js';
  import { hardwareState } from '../stores/hardware.svelte.js';
</script>

<footer class="h-8 bg-gray-900 text-gray-400 flex items-center px-4 text-sm">
  <span class="flex-1">后端: {appState.backendReady ? '✓ 已连接' : '✗ 未连接'}</span>
  <span>Ollama: {hardwareState.ollamaConnected ? '✓' : '✗'} {hardwareState.selectedModel || '未选择模型'}</span>
</footer>
