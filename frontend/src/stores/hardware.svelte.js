export const hardwareState = $state({
  detected: false,
  cpuCores: 0,
  totalMemoryGB: 0,
  gpuMemoryGB: 0,
  gpuAvailable: false,
  recommendedModels: [],
  selectedModel: '',
  selectedEmbeddingModel: 'nomic-embed-text',
  ollamaConnected: false,
  ollamaModels: [],
});
