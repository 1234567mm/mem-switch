// frontend/src/stores/search.svelte.js

const STORAGE_KEY = 'search_scopes';

function loadScopesFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch {}
  return { memory: true, knowledge: true };
}

let debounceTimer = null;

// 状态
let searchState = $state({
  isOpen: false,
  query: '',
  scopes: loadScopesFromStorage(),
  results: { memory: [], knowledge: [] },
  history: [],
  hot: { memory: [], knowledge: [] },
  loading: false,
  expandedScopes: { memory: true, knowledge: true }
});

// 方法
export function toggleSearch() {
  searchState.isOpen = !searchState.isOpen;
}

export function setQuery(q) {
  searchState.query = q;
  if (debounceTimer) clearTimeout(debounceTimer);
  if (q.trim()) {
    debounceTimer = setTimeout(() => search(), 300);
  }
}

export function toggleScope(scope) {
  if (scope in searchState.scopes) {
    searchState.scopes[scope] = !searchState.scopes[scope];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(searchState.scopes));
  }
}

export async function search() {
  if (!searchState.query.trim()) return;
  searchState.loading = true;
  try {
    const resp = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8765'}/api/search/unified`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: searchState.query,
        scopes: searchState.scopes,
        limit: 20
      }),
    });
    const data = await resp.json();
    searchState.results = { memory: data.memory || [], knowledge: data.knowledge || [] };
  } catch (e) {
    console.error('Search failed:', e);
  }
  searchState.loading = false;
}

export async function loadHistory() {
  try {
    const resp = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8765'}/api/search/history?limit=10`);
    const data = await resp.json();
    searchState.history = data.history || [];
  } catch (e) {
    console.error('Failed to load history:', e);
  }
}

export async function loadHot() {
  try {
    const [memoryResp, knowledgeResp] = await Promise.all([
      fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8765'}/api/search/hot?scope=memory&limit=5`),
      fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8765'}/api/search/hot?scope=knowledge&limit=5`),
    ]);
    const [memoryData, knowledgeData] = await Promise.all([
      memoryResp.json(),
      knowledgeResp.json(),
    ]);
    searchState.hot = {
      memory: memoryData.hot || [],
      knowledge: knowledgeData.hot || [],
    };
  } catch (e) {
    console.error('Failed to load hot:', e);
  }
}

export { searchState };