from .base_adapter import BaseAdapter, Conversation, ImportResult
from .claude_code_adapter import ClaudeCodeAdapter
from .claude_mem_adapter import ClaudeMemAdapter
from .codex_adapter import CodexAdapter
from .openclaw_adapter import OpenClawAdapter
from .opencode_adapter import OpenCodeAdapter
from .gemini_cli_adapter import GeminiCLIAdapter
from .hermes_adapter import HermesAdapter
from .json_file_adapter import JSONFileAdapter
from .markdown_adapter import MarkdownAdapter
from .clipboard_adapter import ClipboardAdapter
from .generic_adapter import GenericAdapter


ADAPTERS = {
    'claude_code': ClaudeCodeAdapter,
    'claude_mem': ClaudeMemAdapter,
    'codex': CodexAdapter,
    'openclaw': OpenClawAdapter,
    'opencode': OpenCodeAdapter,
    'gemini_cli': GeminiCLIAdapter,
    'hermes': HermesAdapter,
    'json_file': JSONFileAdapter,
    'markdown': MarkdownAdapter,
    'clipboard': ClipboardAdapter,
    'generic': GenericAdapter,
}


def get_adapter(source_type: str) -> BaseAdapter:
    """Get adapter instance for source type"""
    adapter_class = ADAPTERS.get(source_type, GenericAdapter)
    return adapter_class()
