import { api } from '../lib/api.js';
import { addToast } from './toast.svelte.js';

// Onboarding 状态
let onboardingState = $state({
  // 是否首次启动
  isFirstRun: true,
  // 当前步骤 (0-4)
  currentStep: 0,
  // 是否完成
  completed: false,
  // Ollama 状态
  ollamaConnected: false,
  ollamaUrl: 'http://localhost:11434',
  // 模型状态
  selectedModel: '',
  selectedEmbeddingModel: 'nomic-embed-text',
  availableModels: [],
  // 导入状态
  hasImportedData: false,
});

// 步骤定义
const steps = [
  { id: 0, name: 'welcome', title: '欢迎使用 Mem-Switch' },
  { id: 1, name: 'ollama', title: '配置 Ollama' },
  { id: 2, name: 'model', title: '选择模型' },
  { id: 3, name: 'import', title: '导入数据' },
  { id: 4, name: 'complete', title: '开始使用' },
];

export function nextStep() {
  if (onboardingState.currentStep < steps.length - 1) {
    onboardingState.currentStep++;
  }
}

export function prevStep() {
  if (onboardingState.currentStep > 0) {
    onboardingState.currentStep--;
  }
}

export function goToStep(step) {
  onboardingState.currentStep = step;
}

export async function checkOllamaConnection() {
  try {
    const resp = await api.ollama.status();
    onboardingState.ollamaConnected = resp.data.connected;
    if (resp.data.connected) {
      const modelsResp = await api.ollama.models();
      onboardingState.availableModels = modelsResp.data.map(m => m.name);
      if (!onboardingState.selectedModel && onboardingState.availableModels.length > 0) {
        onboardingState.selectedModel = onboardingState.availableModels[0];
      }
      addToast('Ollama 已连接', 'success');
    } else {
      addToast('Ollama 未连接', 'warning');
    }
  } catch (e) {
    onboardingState.ollamaConnected = false;
    addToast('无法连接到 Ollama', 'error');
  }
}

export async function setOllamaUrl(url) {
  onboardingState.ollamaUrl = url;
  // 更新后端配置
  try {
    const settings = await api.settings.get();
    await api.settings.update({ ...settings.data, ollama_host: url });
    await checkOllamaConnection();
  } catch {
    // 静默失败
  }
}

export function selectModel(model) {
  onboardingState.selectedModel = model;
}

export function selectEmbeddingModel(model) {
  onboardingState.selectedEmbeddingModel = model;
}

export function markDataImported() {
  onboardingState.hasImportedData = true;
}

export async function completeOnboarding() {
  onboardingState.completed = true;
  onboardingState.isFirstRun = false;
  addToast('欢迎使用 Mem-Switch！', 'success');
}

export function resetOnboarding() {
  onboardingState.isFirstRun = true;
  onboardingState.completed = false;
  onboardingState.currentStep = 0;
  onboardingState.hasImportedData = false;
}

export { onboardingState, steps };
