<script>
  import { searchState, toggleSearch, setQuery, toggleScope, search } from '../../stores/search.svelte.js';
  import SearchInput from './SearchInput.svelte';
  import ScopeSelector from './ScopeSelector.svelte';
  import SearchResults from './SearchResults.svelte';
  import SearchHistory from './SearchHistory.svelte';
  import HotItems from './HotItems.svelte';

  function handleInput(q) {
    setQuery(q);
    if (q.trim()) search();
  }
</script>

{#if searchState.isOpen}
<div class="w-96 h-full bg-white border-l border-gray-200 shadow-lg flex flex-col">
  <!-- Header -->
  <div class="p-4 border-b border-gray-100">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-800">搜索</h3>
      <button class="text-gray-400 hover:text-gray-600" onclick={toggleSearch}>×</button>
    </div>
    <SearchInput query={searchState.query} onInput={handleInput} />
    <div class="mt-3">
      <ScopeSelector scopes={searchState.scopes} onToggle={toggleScope} />
    </div>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-auto p-4">
    {#if searchState.loading}
      <div class="text-center py-8 text-gray-500">搜索中...</div>
    {:else if searchState.query && (searchState.results.memory.length > 0 || searchState.results.knowledge.length > 0)}
      <SearchResults results={searchState.results} />
    {:else if searchState.query}
      <div class="text-center py-8 text-gray-400">未找到结果</div>
    {:else}
      <SearchHistory items={searchState.history} />
      <div class="mt-6">
        <HotItems items={searchState.hot} />
      </div>
    {/if}
  </div>
</div>
{/if}
