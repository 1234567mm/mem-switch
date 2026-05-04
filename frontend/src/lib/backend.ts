import { Command } from '@tauri-apps/plugin-shell';

const BACKEND_PORT = parseInt(import.meta.env.VITE_BACKEND_PORT || '8000');
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const QDRANT_URL = 'http://127.0.0.1:6333';
const HEALTH_ENDPOINT = `${BACKEND_URL}/api/health`;

export interface BackendStatus {
  started: boolean;
  error?: string;
}

let backendChild: { pid: number; kill: () => Promise<void> } | null = null;

/**
 * 启动 Python 后端 Sidecar
 */
export async function startBackend(): Promise<void> {
  console.log('[Backend] Starting Python sidecar...');

  try {
    // 使用 Tauri Command.sidecar() 启动后端
    const command = Command.sidecar('binaries/mem-switch-backend');

    // 监听 stdout/stderr
    command.stdout.on('data', (line) => {
      console.log('[Backend stdout]', line);
    });

    command.stderr.on('data', (line) => {
      console.error('[Backend stderr]', line);
    });

    // 启动进程，传递环境变量
    const child = await command.spawn();
    backendChild = child;
    console.log('[Backend] Process spawned with PID:', child.pid);

    // 轮询健康检查
    const maxRetries = 30;
    const retryInterval = 1000; // 1 second

    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(HEALTH_ENDPOINT);
        if (response.ok) {
          console.log('[Backend] Ready after', i + 1, 'retries');
          return;
        }
      } catch (e) {
        // Not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, retryInterval));
    }

    throw new Error('Backend failed to become ready after 30 seconds');
  } catch (error) {
    console.error('[Backend] Start error:', error);
    throw error;
  }
}

/**
 * 停止 Python 后端
 */
export async function stopBackend(): Promise<void> {
  console.log('[Backend] Stopping...');
  if (backendChild) {
    try {
      await backendChild.kill();
      console.log('[Backend] Process killed');
    } catch (error) {
      console.error('[Backend] Kill error:', error);
    }
    backendChild = null;
  }
}

/**
 * 检测 Qdrant 是否可用
 */
export async function checkQdrant(url: string = QDRANT_URL): Promise<boolean> {
  try {
    const response = await fetch(`${url}/healthz`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000)
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * 检查 Docker 是否可用
 */
export async function checkDocker(): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:2375/version', {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    return response.ok;
  } catch {
    // Docker CLI check as fallback
    try {
      const proc = Command.create('docker', ['--version']);
      const output = await proc.execute();
      return output.code === 0;
    } catch {
      return false;
    }
  }
}

/**
 * 一键启动 Qdrant Docker 容器
 */
export async function startQdrantDocker(): Promise<void> {
  console.log('[Qdrant] Starting Docker container...');

  // 检查是否已有同名容器
  const checkCmd = Command.create('docker', ['ps', '-a', '--filter', 'name=mem-switch-qdrant', '-q']);
  const checkResult = await checkCmd.execute();

  if (checkResult.stdout.trim()) {
    // 容器已存在，启动它
    const startCmd = Command.create('docker', ['start', 'mem-switch-qdrant']);
    await startCmd.execute();
    console.log('[Qdrant] Existing container started');
  } else {
    // 创建新容器
    const runCmd = Command.create('docker', [
      'run', '-d',
      '--name', 'mem-switch-qdrant',
      '-p', '6333:6333',
      '-p', '6334:6334',
      '--restart', 'unless-stopped',
      'qdrant/qdrant:latest'
    ]);
    await runCmd.execute();
    console.log('[Qdrant] New container created');
  }

  // 等待 Qdrant 就绪
  const maxRetries = 15;
  for (let i = 0; i < maxRetries; i++) {
    const ok = await checkQdrant();
    if (ok) {
      console.log('[Qdrant] Ready after', i + 1, 'retries');
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  throw new Error('Qdrant failed to become ready');
}

/**
 * 注册应用退出时自动清理
 */
export function registerCleanup(): void {
  window.addEventListener('beforeunload', () => {
    stopBackend();
  });
}
