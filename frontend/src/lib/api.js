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
  },
  channels: {
    list: () => getApi().get('/api/channels'),
    update: (channelId, data) => getApi().put(`/api/channels/${channelId}`, data),
    switch: (channelId, channelType) => getApi().post(`/api/channels/${channelId}/switch`, { channel_type: channelType }),
  },
};
