<script>
    import { channelsState, loadChannels, switchChannel, updateChannel } from '../stores/channels.svelte.js';
    import { onMount } from 'svelte';

    const channelLabels = {
        'claude_code': 'Claude Code',
        'codex': 'Codex',
        'openclaw': 'OpenClaw',
        'opencode': 'OpenCode',
        'gemini_cli': 'Gemini CLI',
        'hermes': 'Hermes',
    };

    let saving = $state({});

    onMount(() => {
        loadChannels();
    });

    async function handleSwitch(platform, event) {
        const channelType = event.target.value;
        await switchChannel(platform, channelType);
    }

    async function handleSave(platform) {
        saving[platform] = true;
        const channel = channelsState.channels.find(c => c.platform === platform);
        if (channel) {
            await updateChannel(platform, {
                recall_count: channel.config.recall_count,
                similarity_threshold: channel.config.similarity_threshold,
                injection_position: channel.config.injection_position,
            });
        }
        saving[platform] = false;
    }
</script>

<div class="max-w-4xl mx-auto p-8">
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-bold">记忆通道路由</h1>
        <label class="flex items-center gap-2">
            <span class="text-sm">全局开关</span>
            <input
                type="checkbox"
                checked={channelsState.globalEnabled}
                class="w-5 h-5"
            />
        </label>
    </div>

    {#if channelsState.loading}
        <p class="text-gray-500">加载中...</p>
    {:else if channelsState.error}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {channelsState.error}
        </div>
    {:else}
        <div class="space-y-4">
            {#each channelsState.channels as channel}
                <div class="bg-white border rounded-lg p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-lg font-semibold">
                            {channelLabels[channel.platform] || channel.platform}
                        </h3>
                        <select
                            class="border rounded px-3 py-1"
                            value={channel.channel_type}
                            onchange={(e) => handleSwitch(channel.platform, e)}
                        >
                            <option value="default">默认通道</option>
                            <option value="mem_switch">Mem-Switch 通道</option>
                        </select>
                    </div>

                    {#if channel.channel_type === 'mem_switch'}
                        <div class="grid grid-cols-3 gap-4 mt-4">
                            <div>
                                <label class="block text-sm font-medium mb-1">召回数量</label>
                                <input
                                    type="number"
                                    class="w-full border rounded px-2 py-1"
                                    bind:value={channel.config.recall_count}
                                />
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1">相似度阈值</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="1"
                                    class="w-full border rounded px-2 py-1"
                                    bind:value={channel.config.similarity_threshold}
                                />
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-1">注入位置</label>
                                <select
                                    class="w-full border rounded px-2 py-1"
                                    bind:value={channel.config.injection_position}
                                >
                                    <option value="system">system prompt</option>
                                    <option value="context_prefix">context prefix</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button
                                class="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                                onclick={() => handleSave(channel.platform)}
                                disabled={saving[channel.platform]}
                            >
                                {saving[channel.platform] ? '保存中...' : '保存配置'}
                            </button>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>