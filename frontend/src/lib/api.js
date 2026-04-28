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
};
