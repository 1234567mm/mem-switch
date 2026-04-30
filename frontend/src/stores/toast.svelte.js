// Toast 通知状态管理
let toastState = $state({
  toasts: []
});

let toastId = 0;

export function addToast(message, type = 'info', duration = 4000, options = {}) {
  const id = ++toastId;
  toastState.toasts = [...toastState.toasts, {
    id,
    message,
    type,
    title: options.title,
    action: options.action,
    persist: options.persist || false
  }];

  if (duration > 0 && !options.persist) {
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }

  return id;
}

export function removeToast(id) {
  toastState.toasts = toastState.toasts.filter(t => t.id !== id);
}

// 快捷方法
export function addSuccessToast(message, options = {}) {
  return addToast(message, 'success', 4000, { ...options, title: '成功' });
}

export function addErrorToast(message, options = {}) {
  return addToast(message, 'error', 6000, { ...options, title: '错误' });
}

export function addWarningToast(message, options = {}) {
  return addToast(message, 'warning', 5000, { ...options, title: '警告' });
}

export function addInfoToast(message, options = {}) {
  return addToast(message, 'info', 4000, { ...options, title: '提示' });
}

export { toastState };
