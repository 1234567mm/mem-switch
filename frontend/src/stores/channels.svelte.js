// frontend/src/stores/channels.svelte.js

export const channelsState = $state({
    channels: [],
    loading: false,
    error: null,
    globalEnabled: true,
});

export async function loadChannels() {
    channelsState.loading = true;
    channelsState.error = null;
    try {
        const resp = await fetch('http://127.0.0.1:8765/api/channels');
        const data = await resp.json();
        channelsState.channels = data.channels;
        channelsState.globalEnabled = data.global_enabled;
    } catch (e) {
        channelsState.error = 'Failed to load channels: ' + e.message;
    }
    channelsState.loading = false;
}

export async function updateChannel(platform, updates) {
    try {
        const resp = await fetch(`http://127.0.0.1:8765/api/channels/${platform}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(updates),
        });
        if (!resp.ok) throw new Error('Update failed');
        await loadChannels();
        return true;
    } catch (e) {
        channelsState.error = 'Failed to update channel: ' + e.message;
        return false;
    }
}

export async function switchChannel(platform, channelType) {
    try {
        const resp = await fetch(`http://127.0.0.1:8765/api/channels/${platform}/switch`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({channel_type: channelType}),
        });
        if (!resp.ok) throw new Error('Switch failed');
        await loadChannels();
        return true;
    } catch (e) {
        channelsState.error = 'Failed to switch channel: ' + e.message;
        return false;
    }
}