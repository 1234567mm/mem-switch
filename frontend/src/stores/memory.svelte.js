// frontend/src/stores/memory.svelte.js

let memoryState = $state({
  memories: [],
  selectedMemory: null,
  editingMemory: null,
  mergeSuggestions: [],
  loading: false
});

export function selectMemory(memory) {
  memoryState.selectedMemory = memory;
}

export function setEditingMemory(memory) {
  memoryState.editingMemory = memory;
}

export function clearEditingMemory() {
  memoryState.editingMemory = null;
}

export function updateMemoryInList(memoryId, updates) {
  memoryState.memories = memoryState.memories.map(m =>
    m.memory_id === memoryId ? { ...m, ...updates } : m
  );
}

export function removeMemoryFromList(memoryId) {
  memoryState.memories = memoryState.memories.filter(m => m.memory_id !== memoryId);
}

export { memoryState };
