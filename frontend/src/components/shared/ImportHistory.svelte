<script>
  import { api } from '../../lib/api.js';
  import StatusBadge from './StatusBadge.svelte';

  let importHistory = $state([]);
  let loading = $state(false);
  let expandedTask = $state(null);

  async function loadHistory() {
    loading = true;
    try {
      const resp = await api.import.getTasks();
      importHistory = resp.data.slice(0, 20);
    } catch (e) {
      console.error('Failed to load import history:', e);
    }
    loading = false;
  }

  function toggleExpand(taskId) {
    expandedTask = expandedTask === taskId ? null : taskId;
  }

  function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN');
  }

  function getStatusText(task) {
    if (task.status === 'completed') return '已完成';
    if (task.status === 'failed') return '失败';
    if (task.status === 'processing') return '处理中';
    if (task.status === 'pending') return '等待中';
    return task.status;
  }

  function getStatusForBadge(task) {
    if (task.status === 'completed') return 'success';
    if (task.status === 'failed') return 'error';
    if (task.status === 'processing') return 'syncing';
    if (task.status === 'pending') return 'idle';
    return 'idle';
  }

  $effect(() => {
    loadHistory();
    const interval = setInterval(loadHistory, 30000);
    return () => clearInterval(interval);
  });
</script>

<div class="bg-white rounded-lg shadow p-4">
  <div class="flex justify-between items-center mb-4">
    <h3 class="font-semibold text-gray-800">导入历史</h3>
    <button
      class="text-sm text-blue-600 hover:text-blue-800"
      onclick={loadHistory}
      disabled={loading}
    >
      {loading ? '刷新中...' : '刷新'}
    </button>
  </div>

  {#if importHistory.length === 0}
    <p class="text-gray-400 text-sm text-center py-4">暂无导入记录</p>
  {:else}
    <div class="space-y-2">
      {#each importHistory as task}
        <div class="border rounded-lg overflow-hidden">
          <button
            class="w-full p-3 flex justify-between items-center hover:bg-gray-50 transition"
            onclick={() => toggleExpand(task.task_id)}
          >
            <div class="flex items-center gap-3">
              <StatusBadge status={getStatusForBadge(task)} text={getStatusText(task)} />
              <span class="text-sm font-medium text-gray-700">
                {task.platform || '未知平台'} - {task.filename || '未知文件'}
              </span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-gray-400">{formatTime(task.created_at)}</span>
              <span class="text-gray-400">{expandedTask === task.task_id ? '▲' : '▼'}</span>
            </div>
          </button>

          {#if expandedTask === task.task_id}
            <div class="p-3 bg-gray-50 border-t">
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span class="text-gray-500">任务ID:</span>
                  <span class="ml-2 font-mono text-xs">{task.task_id}</span>
                </div>
                <div>
                  <span class="text-gray-500">状态:</span>
                  <span class="ml-2">{task.status}</span>
                </div>
                <div>
                  <span class="text-gray-500">文件数:</span>
                  <span class="ml-2">{task.file_count || 0}</span>
                </div>
                <div>
                  <span class="text-gray-500">记忆数:</span>
                  <span class="ml-2">{task.memory_count || 0}</span>
                </div>
                {#if task.error}
                  <div class="col-span-2 text-red-600">
                    <span class="text-gray-500">错误:</span>
                    <span class="ml-2">{task.error}</span>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>