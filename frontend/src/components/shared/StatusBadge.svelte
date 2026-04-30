<script>
  let { status = 'idle', text = '' } = $props();

  const statusConfig = {
    idle: { bg: 'bg-gray-100', text: 'text-gray-600', icon: '○' },
    syncing: { bg: 'bg-blue-100', text: 'text-blue-600', icon: '↻' },
    success: { bg: 'bg-green-100', text: 'text-green-600', icon: '✓' },
    error: { bg: 'bg-red-100', text: 'text-red-600', icon: '✕' },
    warning: { bg: 'bg-amber-100', text: 'text-amber-600', icon: '⚠' },
  };

  let config = $derived(statusConfig[status] || statusConfig.idle);
</script>

<span class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium {config.bg} {config.text}">
  <span class="animate-spin-medium">{config.icon}</span>
  {text || (status === 'idle' ? '就绪' : status === 'syncing' ? '同步中' : status === 'success' ? '已完成' : status === 'error' ? '失败' : status)}
</span>

<style>
  .animate-spin-medium {
    animation: spin 1s linear infinite;
  }
</style>