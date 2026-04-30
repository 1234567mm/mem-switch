from pydantic import BaseModel
from typing import List, Optional


class BatchImportRequest(BaseModel):
    """批量导入请求"""
    source_type: str
    source_path: str
    extract_memories: bool = True
    extract_dimensions: Optional[List[str]] = None
    delete_after_import: bool = False


class TaskFileStatusResponse(BaseModel):
    """单个文件的状态"""
    file_name: str
    status: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    memories_created: int = 0


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    source_type: str
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int
    status: str
    progress: float
    created_at: str
    updated_at: str
    files: Optional[List[TaskFileStatusResponse]] = None


class TaskListItemResponse(BaseModel):
    """任务列表项响应"""
    task_id: str
    source_type: str
    total_files: int
    completed_files: int
    failed_files: int
    skipped_files: int
    status: str
    progress: float
    created_at: str


class RetryTaskRequest(BaseModel):
    """重试任务请求"""
    retry_failed_only: bool = True
