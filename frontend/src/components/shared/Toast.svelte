<script>
  import { removeToast } from '../../stores/toast.svelte.js';

  let { id, message, type = 'info' } = $props();

  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };

  const styles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  };

  const iconStyles = {
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-amber-500',
    info: 'text-blue-500'
  };
</script>

<div class="flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg bg-white {styles[type]}">
  <span class="text-lg {iconStyles[type]}">{icons[type]}</span>
  <span class="font-medium">{message}</span>
  <button
    class="ml-2 opacity-60 hover:opacity-100 transition-opacity"
    onclick={() => removeToast(id)}
  >
    ×
  </button>
</div>
