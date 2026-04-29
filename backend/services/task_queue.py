# backend/services/task_queue.py

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime


class TaskStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    task_id: str
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class TaskQueue:
    """asyncio 后台任务队列"""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: dict[str, Task] = {}
        self._worker: Optional[asyncio.Task] = None

    async def enqueue(self, func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = Task(task_id=task_id)
        await self._queue.put((task_id, func, args, kwargs))

        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._process_queue())

        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def _process_queue(self):
        while True:
            try:
                task_id, func, args, kwargs = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.PROCESSING
                try:
                    result = await func(*args, **kwargs)
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.progress = 1.0
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)

            self._queue.task_done()


task_queue = TaskQueue()
