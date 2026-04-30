<script>
  import { toastState, removeToast } from '../stores/toast.svelte.js';

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const styles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  };
</script>

<div class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
  {#each toastState.toasts as toast (toast.id)}
    <div
      class="flex items-start gap-3 p-4 rounded-lg border shadow-lg bg-white animate-slide-in"
      class:slide-in-enter={true}
    >
      <!-- Icon -->
      <div class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold
        {toast.type === 'success' ? 'bg-green-100 text-green-600' : ''}
        {toast.type === 'error' ? 'bg-red-100 text-red-600' : ''}
        {toast.type === 'warning' ? 'bg-amber-100 text-amber-600' : ''}
        {toast.type === 'info' ? 'bg-blue-100 text-blue-600' : ''}">
        {icons[toast.type]}
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        {#if toast.title}
          <div class="font-semibold text-sm mb-1">{toast.title}</div>
        {/if}
        <div class="text-sm">{toast.message}</div>

        {#if toast.action}
          <div class="mt-2">
            <button
              class="text-xs font-medium underline hover:no-underline"
              onclick={toast.action.onClick}
            >
              {toast.action.label}
            </button>
          </div>
        {/if}
      </div>

      <!-- Close Button -->
      <button
        class="flex-shrink-0 text-gray-400 hover:text-gray-600 text-lg leading-none"
        onclick={() => removeToast(toast.id)}
      >
        ×
      </button>
    </div>
  {/each}
</div>

<style>
  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }
</style>
