"""超时处理器测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository
from src.services.feishu_client import FeishuClient
from src.services.harness_client import HarnessClient
from src.services.timeout_handler import TimeoutHandler, TimeoutResult


@pytest.fixture
def mock_task_repository():
    """模拟任务仓库"""
    return MagicMock(spec=TaskRepository)


@pytest.fixture
def mock_feishu_client():
    """模拟飞书客户端"""
    return MagicMock(spec=FeishuClient)


@pytest.fixture
def mock_harness_client():
    """模拟Harness客户端"""
    return MagicMock(spec=HarnessClient)


@pytest.fixture
def handler(mock_task_repository, mock_feishu_client, mock_harness_client):
    """创建超时处理器实例"""
    return TimeoutHandler(
        task_repository=mock_task_repository,
        feishu_client=mock_feishu_client,
        harness_client=mock_harness_client,
        max_retry_count=3,
    )


@pytest.fixture
def sample_timeout_task():
    """示例超时任务"""
    task = Task()
    task.id = 'task_123'
    task.harness_task_id = 'TASK-123'
    task.content = '测试任务内容'
    task.status = TaskStatus.SENT
    task.feishu_message_id = 'msg_123'
    task.user_id = 'user_123'
    task.retry_count = 0
    task.timeout_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
    return task


class TestCheckTimeoutTasks:
    """测试检查超时任务"""

    def test_check_with_timeout_tasks(self, handler, mock_task_repository, sample_timeout_task):
        """测试检查有超时任务"""
        mock_task_repository.find_timeout_tasks.return_value = [sample_timeout_task]
        mock_task_repository.save.return_value = sample_timeout_task

        results = handler.check_timeout_tasks()

        assert len(results) == 1
        assert results[0].success is True
        mock_task_repository.find_timeout_tasks.assert_called_once()

    def test_check_without_timeout_tasks(self, handler, mock_task_repository):
        """测试检查无超时任务"""
        mock_task_repository.find_timeout_tasks.return_value = []

        results = handler.check_timeout_tasks()

        assert len(results) == 0


class TestHandleTimeoutTask:
    """测试处理超时任务"""

    def test_handle_sent_timeout(self, handler, mock_task_repository, sample_timeout_task):
        """测试处理已发送状态的超时任务"""
        mock_task_repository.save.return_value = sample_timeout_task

        result = handler.handle_timeout_task(sample_timeout_task)

        assert result.success is True
        assert result.action == 'reminder'
        assert sample_timeout_task.retry_count == 1

    def test_handle_max_retries_exceeded(self, handler, mock_task_repository, sample_timeout_task):
        """测试超过最大重试次数"""
        sample_timeout_task.retry_count = 3
        mock_task_repository.save.return_value = sample_timeout_task

        result = handler.handle_timeout_task(sample_timeout_task)

        assert result.success is True
        assert result.action == 'failed'
        assert sample_timeout_task.status == TaskStatus.FAILED

    def test_handle_other_status(self, handler, sample_timeout_task):
        """测试其他状态的任务"""
        sample_timeout_task.status = TaskStatus.COMPLETED

        result = handler.handle_timeout_task(sample_timeout_task)

        assert result.success is True
        assert result.action == 'skipped'


class TestSendTimeoutReminder:
    """测试发送超时提醒"""

    def test_send_reminder_success(self, handler, mock_feishu_client, sample_timeout_task):
        """测试发送提醒成功"""
        result = handler.send_timeout_reminder(sample_timeout_task)

        assert result is True

    def test_send_reminder_no_feishu_client(self, mock_task_repository, sample_timeout_task):
        """测试没有飞书客户端"""
        handler = TimeoutHandler(task_repository=mock_task_repository, feishu_client=None)

        result = handler.send_timeout_reminder(sample_timeout_task)

        assert result is False

    def test_send_reminder_no_message_id(self, handler, sample_timeout_task):
        """测试没有消息ID"""
        sample_timeout_task.feishu_message_id = None

        result = handler.send_timeout_reminder(sample_timeout_task)

        assert result is False


class TestMarkTaskTimeout:
    """测试标记任务超时"""

    def test_mark_timeout_success(self, handler, mock_task_repository, sample_timeout_task):
        """测试标记超时成功"""
        mock_task_repository.save.return_value = sample_timeout_task

        result = handler.mark_task_timeout(sample_timeout_task)

        assert result.success is True
        assert result.action == 'timeout'
        assert sample_timeout_task.status == TaskStatus.TIMEOUT

    def test_mark_timeout_failure(self, handler, mock_task_repository, sample_timeout_task):
        """测试标记超时失败"""
        mock_task_repository.save.side_effect = Exception('Database error')

        result = handler.mark_task_timeout(sample_timeout_task)

        assert result.success is False
        assert result.action == 'timeout'


class TestMarkTaskFailed:
    """测试标记任务失败"""

    def test_mark_failed_success(self, handler, mock_task_repository, sample_timeout_task):
        """测试标记失败成功"""
        mock_task_repository.save.return_value = sample_timeout_task

        result = handler.mark_task_failed(sample_timeout_task)

        assert result.success is True
        assert result.action == 'failed'
        assert sample_timeout_task.status == TaskStatus.FAILED

    def test_mark_failed_failure(self, handler, mock_task_repository, sample_timeout_task):
        """测试标记失败失败"""
        mock_task_repository.save.side_effect = Exception('Database error')

        result = handler.mark_task_failed(sample_timeout_task)

        assert result.success is False
        assert result.action == 'failed'


class TestGetTimeoutStats:
    """测试获取超时统计"""

    def test_get_stats(self, handler, mock_task_repository):
        """测试获取统计信息"""
        mock_task_repository.count_by_status.side_effect = lambda status: {
            TaskStatus.TIMEOUT: 3,
            TaskStatus.FAILED: 2,
            TaskStatus.SENT: 5,
        }.get(status, 0)

        stats = handler.get_timeout_stats()

        assert stats['timeout'] == 3
        assert stats['failed'] == 2
        assert stats['sent'] == 5
        assert stats['pending_timeout_check'] == 5


class TestTimeoutResult:
    """测试超时结果"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = TimeoutResult(
            task_id='task_123',
            action='reminder',
            success=True,
            message='Reminder sent',
        )
        d = result.to_dict()
        assert d['task_id'] == 'task_123'
        assert d['action'] == 'reminder'
        assert d['success'] is True
        assert d['message'] == 'Reminder sent'
