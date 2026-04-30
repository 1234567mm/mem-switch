<script>
  import { api } from '../../lib/api.js';
  import { addToast } from '../../stores/toast.svelte.js';

  let { memory, onClose, onUpdate } = $props();

  let editedType = $state('');
  let editedContent = $state('');
  let saving = $state(false);
  let error = $state('');

  const memoryTypes = [
    { id: 'preference', label: '偏好习惯' },
    { id: 'expertise', label: '专业知识' },
    { id: 'project_context', label: '项目上下文' },
  ];

  $effect(() => {
    if (memory) {
      editedType = memory.type;
      editedContent = memory.content;
      error = '';
    }
  });

  async function handleSave() {
    if (!editedContent.trim()) {
      error = '内容不能为空';
      return;
    }

    saving = true;
    error = '';

    try {
      const updateData = {
        content: editedContent,
        memory_type: editedType,
      };

      await api.memory.update(memory.memory_id, updateData);
      addToast('记忆更新成功', 'success');

      if (onUpdate) {
        onUpdate();
      }

      if (onClose) {
        onClose();
      }
    } catch (e) {
      error = '保存失败: ' + e.message;
      addToast('保存失败: ' + e.message, 'error');
    } finally {
      saving = false;
    }
  }

  function handleCancel() {
    if (onClose) {
      onClose();
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  }
</script>

{#if memory}
  <!-- 遮罩层 -->
  <div
    class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4"
    onclick={handleCancel}
    onkeydown={handleKeydown}
    role="dialog"
    aria-modal="true"
  >
    <!-- 对话框 -->
    <div
      class="bg-white rounded-lg shadow-xl w-full max-w-lg z-50"
      onclick={(e) => e.stopPropagation()}
    >
      <!-- 标题栏 -->
      <div class="flex justify-between items-center p-4 border-b">
        <h2 class="text-lg font-semibold">编辑记忆</h2>
        <button
          class="text-gray-400 hover:text-gray-600 text-xl"
          onclick={handleCancel}
          aria-label="关闭"
        >
          &times;
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="p-4 space-y-4">
        {#if error}
          <div class="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        {/if}

        <!-- 类型选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            记忆类型
          </label>
          <select
            class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            bind:value={editedType}
          >
            {#each memoryTypes as type}
              <option value={type.id}>{type.label}</option>
            {/each}
          </select>
        </div>

        <!-- 内容编辑 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            记忆内容
          </label>
          <textarea
            class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[150px]"
            bind:value={editedContent}
            placeholder="输入记忆内容..."
            onkeydown={handleKeydown}
          ></textarea>
          <p class="text-xs text-gray-500 mt-1">提示：Ctrl+Enter 保存，Esc 取消</p>
        </div>
      </div>

      <!-- 按钮区域 -->
      <div class="flex justify-end gap-3 p-4 border-t bg-gray-50 rounded-b-lg">
        <button
          class="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          onclick={handleCancel}
          disabled={saving}
        >
          取消
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onclick={handleSave}
          disabled={saving}
        >
          {saving ? '保存中...' : '保存'}
        </button>
      </div>
    </div>
  </div>
{/if}
