class MemSwitchError(Exception):
    """Base exception for Mem-Switch"""

    def __init__(self, message: str, request_id: str = None):
        self.message = message
        self.request_id = request_id
        super().__init__(self.message)

class VectorStoreError(MemSwitchError):
    """Vector store operation failed"""
    pass

class OllamaConnectionError(MemSwitchError):
    """Cannot connect to Ollama"""
    pass

class ChannelNotFoundError(MemSwitchError):
    """Channel configuration not found"""
    pass

class MemoryNotFoundError(MemSwitchError):
    """Memory not found"""
    pass

class TaskQueueError(MemSwitchError):
    """Task queue operation failed"""
    pass
