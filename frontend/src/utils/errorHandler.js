/**
 * 错误处理工具
 * 提供统一的错误处理和用户友好的错误消息
 */

const errorMessages = {
  // 网络错误
  'ECONNREFUSED': '无法连接到服务器，请检查后端服务是否运行',
  'ETIMEDOUT': '请求超时，请检查网络连接',
  'ERR_NETWORK': '网络错误，请检查网络连接',

  // Ollama 错误
  'OLLAMA_NOT_FOUND': 'Ollama 未安装或未运行',
  'OLLAMA_CONNECTION_ERROR': '无法连接到 Ollama',
  'MODEL_NOT_FOUND': '模型不存在，请先下载模型',

  // 文件错误
  'FILE_TOO_LARGE': '文件过大，请选择小于 10MB 的文件',
  'INVALID_FILE_TYPE': '不支持的文件类型',
  'FILE_NOT_FOUND': '文件不存在',

  // 数据库错误
  'DATABASE_ERROR': '数据库操作失败',
  'DATABASE_LOCKED': '数据库正忙，请稍后重试',

  // 权限错误
  'PERMISSION_DENIED': '权限不足，请检查文件权限',
  'UNAUTHORIZED': '未授权访问',

  // 默认错误
  'DEFAULT': '操作失败，请稍后重试'
};

/**
 * 从错误对象中提取友好的错误消息
 * @param {Error|any} error - 错误对象
 * @param {string} defaultMsg - 默认错误消息
 * @returns {string} 友好的错误消息
 */
export function getErrorMessage(error, defaultMsg = null) {
  if (!error) return defaultMsg || errorMessages.DEFAULT;

  // 处理字符串错误
  if (typeof error === 'string') {
    return error;
  }

  // 处理 Error 对象
  const message = error.message || String(error);

  // 检查是否有自定义错误消息
  if (error.customMessage) {
    return error.customMessage;
  }

  // 匹配已知错误代码
  for (const [code, msg] of Object.entries(errorMessages)) {
    if (message.includes(code) || message.toUpperCase().includes(code)) {
      return msg;
    }
  }

  // 匹配已知错误模式
  if (message.includes('fetch') || message.includes('network')) {
    return errorMessages['ERR_NETWORK'];
  }

  if (message.includes('timeout')) {
    return errorMessages['ETIMEDOUT'];
  }

  if (message.includes('Ollama')) {
    return errorMessages['OLLAMA_CONNECTION_ERROR'];
  }

  if (message.includes('model')) {
    return errorMessages['MODEL_NOT_FOUND'];
  }

  if (message.includes('file')) {
    return errorMessages['FILE_NOT_FOUND'];
  }

  return defaultMsg || message;
}

/**
 * 处理异步请求错误，自动显示 Toast 通知
 * @param {Function} fn - 异步函数
 * @param {Object} options - 选项
 * @param {string} options.successMessage - 成功消息
 * @param {string} options.errorMessage - 错误消息
 * @param {Function} options.onError - 错误回调
 * @returns {Promise<any>} 异步函数结果
 */
export async function handleAsyncOperation(fn, options = {}) {
  try {
    const result = await fn();
    if (options.successMessage) {
      console.log('Success:', options.successMessage);
    }
    return result;
  } catch (error) {
    const message = getErrorMessage(error, options.errorMessage);
    console.error('Operation failed:', message, error);

    if (options.onError) {
      options.onError(error, message);
    }

    throw error;
  }
}

/**
 * 批量错误处理（用于批量导入等场景）
 * @param {Array} items - 项目列表
 * @param {Function} processor - 处理函数
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<{success: Array, failed: Array}>}
 */
export async function handleBatchOperation(items, processor, onProgress = null) {
  const success = [];
  const failed = [];

  for (let i = 0; i < items.length; i++) {
    try {
      await processor(items[i], i);
      success.push(items[i]);
    } catch (error) {
      failed.push({ item: items[i], error: getErrorMessage(error) });
    }

    if (onProgress) {
      onProgress({
        total: items.length,
        completed: i + 1,
        success: success.length,
        failed: failed.length
      });
    }
  }

  return { success, failed };
}

export default {
  getErrorMessage,
  handleAsyncOperation,
  handleBatchOperation
};
