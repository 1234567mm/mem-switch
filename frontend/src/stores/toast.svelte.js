// Toast 通知状态管理
let toastState = $state({
  toasts: []
});

let toastId = 0;

export function addToast(message, type = 'info', duration = 4000) {
  const id = ++toastId;
  toastState.toasts = [...toastState.toasts, { id, message, type }];

  if (duration > 0) {
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }

  return id;
}

export function removeToast(id) {
  toastState.toasts = toastState.toasts.filter(t => t.id !== id);
}

export { toastState };
