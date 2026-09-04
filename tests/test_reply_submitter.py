"""回复提交服务测试"""

import pytest
from unittest.mock import MagicMock, patch

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository
from src.services.harness_client import HarnessClient, HarnessConnectionError, HarnessAPIError
from src.services.reply_submitter import ReplySubmitter, ReplySubmitResult


@pytest.fixture
def mock_harness_client():
    """模拟Harness客户端"""
    return MagicMock(spec=HarnessClient)


@pytest.fixture
def mock_task_repository():
    """模拟任务仓库"""
    return MagicMock(spec=TaskRepository)


@pytest.fixture
def submitter(mock_harness_client, mock_task_repository):
    """创建回复提交服务实例"""
    return ReplySubmitter(
        harness_client=mock_harness_client,
        task_repository=mock_task_repository,
    )


@pytest.fixture
def sample_task():
    """示例任务"""
    task = Task()
    task.id = 'local_123'
    task.harness_task_id = 'TASK-123'
    task.content = '测试任务'
    task.status = TaskStatus.REPLIED
    task.user_reply = '确认执行'
    task.user_id = 'user_123'
    task.retry_count = 0
    return task


class TestSubmitReply:
    """测试提交回复"""

    def test_submit_success(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试提交成功"""
        mock_task_repository.find_by_id.return_value = sample_task
        mock_harness_client.submit_reply.return_value = True

        result = submitter.submit_reply('local_123', '确认执行', 'user_123')

        assert result.success is True
        assert result.task_id == 'local_123'
        assert result.message == 'Reply submitted successfully'
        mock_task_repository.save.assert_called_once()
        assert sample_task.status == TaskStatus.COMPLETED

    def test_submit_task_not_found(self, submitter, mock_task_repository):
        """测试任务不存在"""
        mock_task_repository.find_by_id.return_value = None
        mock_task_repository.find_by_harness_task_id.return_value = None

        result = submitter.submit_reply('nonexistent', '确认执行', 'user_123')

        assert result.success is False
        assert 'Task not found' in result.message

    def test_submit_wrong_status(self, submitter, mock_task_repository, sample_task):
        """测试任务状态错误"""
        sample_task.status = TaskStatus.SENT
        mock_task_repository.find_by_id.return_value = sample_task

        result = submitter.submit_reply('local_123', '确认执行', 'user_123')

        assert result.success is False
        assert 'expected REPLIED' in result.message

    def test_submit_harness_connection_error(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试Harness连接错误"""
        mock_task_repository.find_by_id.return_value = sample_task
        mock_harness_client.submit_reply.side_effect = HarnessConnectionError('Connection refused')

        result = submitter.submit_reply('local_123', '确认执行', 'user_123')

        assert result.success is False
        assert 'Connection error' in result.message

    def test_submit_harness_api_error(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试Harness API错误"""
        mock_task_repository.find_by_id.return_value = sample_task
        mock_harness_client.submit_reply.side_effect = HarnessAPIError('API error')

        result = submitter.submit_reply('local_123', '确认执行', 'user_123')

        assert result.success is False
        assert 'API error' in result.message

    def test_submit_unexpected_error(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试未预期错误"""
        mock_task_repository.find_by_id.return_value = sample_task
        mock_harness_client.submit_reply.side_effect = Exception('Unexpected')

        result = submitter.submit_reply('local_123', '确认执行', 'user_123')

        assert result.success is False
        assert 'Unexpected error' in result.message

    def test_submit_by_harness_task_id(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试通过harness_task_id提交"""
        mock_task_repository.find_by_id.return_value = None
        mock_task_repository.find_by_harness_task_id.return_value = sample_task
        mock_harness_client.submit_reply.return_value = True

        result = submitter.submit_reply('TASK-123', '确认执行', 'user_123')

        assert result.success is True


class TestSubmitPendingReplies:
    """测试提交待处理回复"""

    def test_submit_pending_success(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试提交待处理回复成功"""
        mock_task_repository.find_by_status.return_value = [sample_task]
        mock_task_repository.find_by_id.return_value = sample_task
        mock_harness_client.submit_reply.return_value = True

        results = submitter.submit_pending_replies()

        assert len(results) == 1
        assert results[0].success is True
        mock_task_repository.find_by_status.assert_called_once_with(TaskStatus.REPLIED)

    def test_submit_pending_empty(self, submitter, mock_task_repository):
        """测试没有待处理回复"""
        mock_task_repository.find_by_status.return_value = []

        results = submitter.submit_pending_replies()

        assert len(results) == 0

    def test_submit_pending_no_reply(self, submitter, mock_task_repository, sample_task):
        """测试任务没有回复内容"""
        sample_task.user_reply = None
        mock_task_repository.find_by_status.return_value = [sample_task]

        results = submitter.submit_pending_replies()

        assert len(results) == 0


class TestRetryFailedSubmissions:
    """测试重试失败提交"""

    def test_retry_success(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试重试成功"""
        mock_task_repository.find_by_status.return_value = [sample_task]
        mock_task_repository.find_by_id.return_value = sample_task
        mock_harness_client.submit_reply.return_value = True

        results = submitter.retry_failed_submissions(max_retries=3)

        assert len(results) == 1
        assert results[0].success is True
        assert sample_task.retry_count == 1

    def test_retry_exceeded_max(self, submitter, mock_task_repository, sample_task):
        """测试超过最大重试次数"""
        sample_task.retry_count = 3
        mock_task_repository.find_by_status.return_value = [sample_task]

        results = submitter.retry_failed_submissions(max_retries=3)

        assert len(results) == 0

    def test_retry_with_failures(self, submitter, mock_harness_client, mock_task_repository, sample_task):
        """测试重试过程中有失败"""
        mock_task_repository.find_by_status.return_value = [sample_task]
        mock_harness_client.submit_reply.side_effect = HarnessConnectionError('Connection refused')

        results = submitter.retry_failed_submissions(max_retries=3)

        assert len(results) == 1
        assert results[0].success is False
        assert sample_task.retry_count == 1


class TestGetSubmissionStats:
    """测试获取提交统计"""

    def test_get_stats(self, submitter, mock_task_repository):
        """测试获取统计信息"""
        mock_task_repository.count_by_status.side_effect = lambda status: {
            TaskStatus.REPLIED: 5,
            TaskStatus.COMPLETED: 10,
            TaskStatus.FAILED: 2,
        }.get(status, 0)

        stats = submitter.get_submission_stats()

        assert stats['replied'] == 5
        assert stats['completed'] == 10
        assert stats['failed'] == 2
        assert stats['pending_submission'] == 5


class TestReplySubmitResult:
    """测试提交结果"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = ReplySubmitResult(
            task_id='TASK-123',
            success=True,
            message='Success',
            harness_response={'status': 'ok'},
        )
        d = result.to_dict()
        assert d['task_id'] == 'TASK-123'
        assert d['success'] is True
        assert d['message'] == 'Success'
        assert d['harness_response'] == {'status': 'ok'}

    def test_to_dict_without_response(self):
        """测试转换为字典（无Harness响应）"""
        result = ReplySubmitResult(
            task_id='TASK-123',
            success=False,
            message='Failed',
        )
        d = result.to_dict()
        assert d['harness_response'] is None
