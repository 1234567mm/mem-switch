import axios from 'axios';
import { appState } from '../stores/app.svelte.js';

function getApi() {
  return axios.create({ baseURL: appState.backendUrl, timeout: 30000 });
}

export const api = {
  health: () => getApi().get('/api/health'),
  hardware: { detect: () => getApi().get('/api/hardware/detect') },
  ollama: {
    status: () => getApi().get('/api/ollama/status'),
    models: () => getApi().get('/api/ollama/models'),
    pull: (name) => getApi().post('/api/ollama/pull', { model: name }),
  },
  settings: {
    get: () => getApi().get('/api/settings'),
    update: (data) => getApi().put('/api/settings', data),
  },
  knowledge: {
    listBases: () => getApi().get('/api/knowledge/bases'),
    createBase: (data) => getApi().post('/api/knowledge/bases', data),
    getBase: (kbId) => getApi().get(`/api/knowledge/bases/${kbId}`),
    deleteBase: (kbId) => getApi().delete(`/api/knowledge/bases/${kbId}`),
    listDocs: (kbId) => getApi().get(`/api/knowledge/bases/${kbId}/documents`),
    search: (kbId, query, limit) => getApi().post(`/api/knowledge/bases/${kbId}/search`, { query, limit }),
    uploadDoc: (kbId, formData) => getApi().post(`/api/knowledge/bases/${kbId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  },
  memory: {
    list: (type) => getApi().get('/api/memory/list', { params: type ? { memory_type: type } : {} }),
    search: (query, type, limit) => getApi().post('/api/memory/search', { query, memory_type: type, limit }),
    delete: (memoryId) => getApi().delete(`/api/memory/${memoryId}`),
    update: (id, data) => getApi().patch(`/api/memory/${id}`, data),
    invalidate: (id, invalidate) => getApi().post(`/api/memory/${id}/invalidate`, { invalidate }),
    getStats: (id) => getApi().get(`/api/memory/${id}/stats`),
    merge: (memoryIds, mergedContent, mergedType) => getApi().post('/api/memory/merge', { memory_ids: memoryIds, merged_content: mergedContent, merged_type: mergedType }),
  },
  channels: {
    list: () => getApi().get('/api/channels'),
    update: (channelId, data) => getApi().put(`/api/channels/${channelId}`, data),
    switch: (channelId, channelType) => getApi().post(`/api/channels/${channelId}/switch`, { channel_type: channelType }),
  },
  import: {
    preview: (sourceType) => getApi().get('/api/import/preview', { params: { source_type: sourceType } }),
    conversations: (sourceType) => getApi().post('/api/import/conversations', { source_type: sourceType, extract_memories: true }),
    uploadFile: (sourceType, formData) => getApi().post(`/api/import/upload?source_type=${sourceType}`, formData),
    // Batch import
    batch: (sourceType, files) => getApi().post('/api/import/batch', { source_type: sourceType, files }),
    listTasks: () => getApi().get('/api/import/tasks'),
    getTaskStatus: (taskId) => getApi().get(`/api/import/tasks/${taskId}`),
    retryFailed: (taskId) => getApi().post(`/api/import/tasks/${taskId}/retry`),
  },
  search: {
    unified: (data) => getApi().post('/api/search/unified', data),
    history: (limit) => getApi().get('/api/search/history', { params: { limit } }),
    hot: (scope, limit) => getApi().get('/api/search/hot', { params: { scope, limit } }),
  },
};
