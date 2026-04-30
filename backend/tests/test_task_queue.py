import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from services.task_queue import TaskQueue, Task, TaskStatus


class TestTaskQueue:
    """TaskQueue 单元测试"""

    @pytest.fixture
    def queue(self):
        return TaskQueue()

    # ── enqueue ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_enqueue_creates_task_id(self, queue):
        """enqueue 应返回有效的 UUID 字符串"""
        async def dummy():
            return "result"
        task_id = await queue.enqueue(dummy)
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_enqueue_stores_task(self, queue):
        """enqueue 应在 _tasks 中创建 Task 条目"""
        async def dummy():
            return "result"
        task_id = await queue.enqueue(dummy)
        task = queue._tasks.get(task_id)
        assert task is not None
        assert task.task_id == task_id
        assert task.status == TaskStatus.QUEUED

    @pytest.mark.asyncio
    async def test_enqueue_starts_worker_when_none(self, queue):
        """enqueue 应在 worker 为 None 时启动 worker"""
        async def dummy():
            return "result"
        assert queue._worker is None
        task_id = await queue.enqueue(dummy)
        assert queue._worker is not None

    @pytest.mark.asyncio
    async def test_enqueue_with_args_and_kwargs(self, queue):
        """enqueue 应正确传递 args 和 kwargs"""
        async def dummy(*args, **kwargs):
            return (args, kwargs)
        task_id = await queue.enqueue(dummy, "a", "b", key="value")
        task = queue._tasks.get(task_id)
        assert task is not None

    # ── get_task_status ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_task_status_found(self, queue):
        """get_task_status 应返回已存在的 Task"""
        async def dummy():
            return "result"
        task_id = await queue.enqueue(dummy)
        status = await queue.get_task_status(task_id)
        assert status is not None
        assert status.task_id == task_id

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, queue):
        """get_task_status 对不存在的 task_id 返回 None"""
        status = await queue.get_task_status("nonexistent-id")
        assert status is None

    # ── _process_queue ───────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_process_queue_handles_exception(self, queue):
        """_process_queue 应捕获异常并设置 FAILED 状态"""
        async def failing_task():
            raise ValueError("test error")
        task_id = await queue.enqueue(failing_task)
        # Wait for worker to process
        await asyncio.sleep(0.2)
        task = queue._tasks.get(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "test error"

    # ── Task dataclass ───────────────────────────────────────────

    def test_task_default_values(self):
        """Task 默认值应正确"""
        task = Task(task_id="test-123")
        assert task.task_id == "test-123"
        assert task.status == TaskStatus.QUEUED
        assert task.progress == 0.0
        assert task.result is None
        assert task.error is None
        assert task.created_at is not None

    def test_task_status_enum(self):
        """TaskStatus 枚举值应正确"""
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
