-- Migration: Add memory management fields
-- Date: 2026-04-30
-- Description: Add fields for memory edit, invalidate, and stats features

-- Add new columns to memories table
ALTER TABLE memories ADD COLUMN invalidated BOOLEAN DEFAULT 0;
ALTER TABLE memories ADD COLUMN expires_at DATETIME;
ALTER TABLE memories ADD COLUMN call_count INTEGER DEFAULT 0;
ALTER TABLE memories ADD COLUMN last_called_at DATETIME;

-- Create index for invalidated status (for filtering)
CREATE INDEX IF NOT EXISTS idx_memories_invalidated ON memories(invalidated);

-- Create index for expires_at (for expiry check)
CREATE INDEX IF NOT EXISTS idx_memories_expires_at ON memories(expires_at);

-- Add new columns to documents table for consistency
ALTER TABLE documents ADD COLUMN view_count INTEGER DEFAULT 0;
ALTER TABLE documents ADD COLUMN last_viewed_at DATETIME;

-- Create search_history table if not exists
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    scope TEXT
);

-- Create index for search history timestamp
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(timestamp DESC);
