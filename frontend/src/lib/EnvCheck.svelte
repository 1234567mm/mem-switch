<script lang="ts">
  import { onMount } from 'svelte';
  import { startBackend, stopBackend, checkQdrant, checkDocker, startQdrantDocker, registerCleanup } from './backend';

  interface Props {
    onReady?: () => void;
  }

  let { onReady }: Props = $props();

  let status = $state('checking');
  let error = $state('');
  let qdrantAvailable = $state(false);
  let dockerAvailable = $state(false);

  onMount(async () => {
    registerCleanup();
    await runChecks();
  });

  async function runChecks() {
    try {
      // 1. 启动后端
      status = 'Starting backend...';
      await startBackend();

      // 2. 检测 Qdrant
      status = 'Checking Qdrant...';
      qdrantAvailable = await checkQdrant();

      if (!qdrantAvailable) {
        status = 'Checking Docker...';
        dockerAvailable = await checkDocker();
      }

      status = qdrantAvailable ? 'Ready!' : 'Needs Qdrant';

      if (status === 'Ready!' && onReady) {
        onReady();
      }
    } catch (e) {
      error = String(e);
      status = 'Error';
    }
  }

  async function handleStartQdrant() {
    try {
      status = 'Starting Qdrant...';
      await startQdrantDocker();
      qdrantAvailable = true;
      status = 'Ready!';
      if (onReady) {
        onReady();
      }
    } catch (e) {
      error = String(e);
    }
  }
</script>

<div class="env-check">
  <h2>Environment Check</h2>
  <p class="status">{status}</p>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  {#if !qdrantAvailable && status !== 'Ready!'}
    <div class="qdrant-section">
      {#if dockerAvailable}
        <button onclick={handleStartQdrant}>
          Start Qdrant Container
        </button>
      {:else}
        <p>Please install Docker Desktop to run Qdrant vector database.</p>
        <a href="https://www.docker.com/products/docker-desktop" target="_blank" rel="noopener noreferrer">
          Download Docker Desktop
        </a>
      {/if}
    </div>
  {/if}
</div>

<style>
  .env-check {
    padding: 2rem;
    text-align: center;
  }
  .status {
    font-size: 1.2rem;
    color: #666;
  }
  .error {
    color: red;
  }
  button {
    padding: 0.5rem 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
