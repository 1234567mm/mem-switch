-- backend/migrations/001_add_channels.sql

-- 通道配置表
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL DEFAULT 'default',
    enabled INTEGER NOT NULL DEFAULT 1,
    auto_record INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 通道参数表
CREATE TABLE IF NOT EXISTS channel_configs (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    recall_count INTEGER NOT NULL DEFAULT 5,
    similarity_threshold REAL NOT NULL DEFAULT 0.7,
    injection_position TEXT NOT NULL DEFAULT 'system',
    max_tokens INTEGER,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

-- 平台设置表
CREATE TABLE IF NOT EXISTS platform_settings (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,
    api_endpoint TEXT,
    config_path TEXT,
    config_backup TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 初始化 6 个平台的默认配置
INSERT OR IGNORE INTO channels (id, platform, channel_type, enabled, auto_record, created_at, updated_at)
VALUES
    ('ch_claude_code', 'claude_code', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_codex', 'codex', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_openclaw', 'openclaw', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_opencode', 'opencode', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_gemini_cli', 'gemini_cli', 'default', 1, 0, datetime('now'), datetime('now')),
    ('ch_hermes', 'hermes', 'default', 1, 0, datetime('now'), datetime('now'));

INSERT OR IGNORE INTO channel_configs (id, channel_id, recall_count, similarity_threshold, injection_position, max_tokens)
VALUES
    ('cc_claude_code', 'ch_claude_code', 5, 0.7, 'system', NULL),
    ('cc_codex', 'ch_codex', 5, 0.7, 'system', NULL),
    ('cc_openclaw', 'ch_openclaw', 5, 0.7, 'system', NULL),
    ('cc_opencode', 'ch_opencode', 5, 0.7, 'system', NULL),
    ('cc_gemini_cli', 'ch_gemini_cli', 5, 0.7, 'system', NULL),
    ('cc_hermes', 'ch_hermes', 5, 0.7, 'system', NULL);