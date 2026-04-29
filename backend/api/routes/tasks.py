# backend/api/routes/tasks.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from services.task_queue import task_queue, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskSubmit(BaseModel):
    task_type: str
    params: dict = {}


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    result: Optional[Any] = None
    error: Optional[str] = None


@router.post("", response_model=dict)
async def submit_task(data: TaskSubmit):
    task_id = await task_queue.enqueue(_process_task, data.task_type, data.params)
    return {"task_id": task_id, "status": "queued"}


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task = await task_queue.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        progress=task.progress,
        result=task.result,
        error=task.error,
    )


async def _process_task(task_type: str, params: dict) -> dict:
    return {"status": "processed", "type": task_type}
