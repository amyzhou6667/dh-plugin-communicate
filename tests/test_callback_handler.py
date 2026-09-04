"""回调处理器测试"""

import pytest
from unittest.mock import MagicMock, patch

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository
from src.services.callback_handler import CallbackHandler, CallbackResult, CallbackStatus
from src.services.callback_parser import FeishuCallbackParser, FeishuMessageEvent
from src.services.harness_client import HarnessClient


@pytest.fixture
def mock_callback_parser():
    """模拟回调解析器"""
    return MagicMock(spec=FeishuCallbackParser)


@pytest.fixture
def mock_task_repository():
    """模拟任务仓库"""
    return MagicMock(spec=TaskRepository)


@pytest.fixture
def mock_harness_client():
    """模拟Harness客户端"""
    return MagicMock(spec=HarnessClient)


@pytest.fixture
def handler(mock_callback_parser, mock_task_repository, mock_harness_client):
    """创建回调处理器实例"""
    return CallbackHandler(
        callback_parser=mock_callback_parser,
        task_repository=mock_task_repository,
        harness_client=mock_harness_client,
    )


@pytest.fixture
def sample_event():
    """示例消息事件"""
    return FeishuMessageEvent(
        message_id='msg_123',
        chat_id='chat_123',
        chat_type='p2p',
        message_type='text',
        content='确认 TASK-123',
        sender_open_id='ou_user_123',
        create_time='1234567890',
    )


@pytest.fixture
def sample_task():
    """示例任务"""
    task = Task()
    task.id = 'local_123'
    task.harness_task_id = 'TASK-123'
    task.content = '测试任务'
    task.status = TaskStatus.SENT
    return task


@pytest.fixture
def sample_callback_data():
    """示例回调数据"""
    return {
        'schema': '2.0',
        'header': {
            'event_type': 'im.message.receive_v1',
        },
        'event': {
            'sender': {
                'sender_id': {'open_id': 'ou_user_123'},
            },
            'message': {
                'message_id': 'msg_123',
                'chat_id': 'chat_123',
                'chat_type': 'p2p',
                'message_type': 'text',
                'content': '{"text":"确认 TASK-123"}',
            },
        },
    }


class TestHandleMessageCallback:
    """测试处理消息回调"""

    def test_handle_success(self, handler, mock_callback_parser, mock_task_repository, sample_event, sample_task):
        """测试处理成功"""
        mock_callback_parser.parse_message_event.return_value = sample_event
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = sample_task

        result = handler.handle_message_callback({'test': 'data'})

        assert result.success is True
        assert result.status == CallbackStatus.SUCCESS
        assert result.task_id == 'TASK-123'
        mock_task_repository.save.assert_called_once()

    def test_handle_parse_failed(self, handler, mock_callback_parser):
        """测试解析失败"""
        mock_callback_parser.parse_message_event.return_value = None

        result = handler.handle_message_callback({'test': 'data'})

        assert result.success is False
        assert result.status == CallbackStatus.INVALID_DATA

    def test_handle_no_task_id(self, handler, mock_callback_parser, sample_event):
        """测试没有任务ID"""
        mock_callback_parser.parse_message_event.return_value = sample_event
        mock_callback_parser.extract_task_id_from_message.return_value = None

        result = handler.handle_message_callback({'test': 'data'})

        assert result.success is False
        assert result.status == CallbackStatus.TASK_NOT_FOUND

    def test_handle_task_not_found(self, handler, mock_callback_parser, mock_task_repository, sample_event):
        """测试任务未找到"""
        mock_callback_parser.parse_message_event.return_value = sample_event
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = None
        mock_task_repository.find_by_id.return_value = None

        result = handler.handle_message_callback({'test': 'data'})

        assert result.success is False
        assert result.status == CallbackStatus.TASK_NOT_FOUND
        assert result.task_id == 'TASK-123'

    def test_handle_save_failed(self, handler, mock_callback_parser, mock_task_repository, sample_event, sample_task):
        """测试保存失败"""
        mock_callback_parser.parse_message_event.return_value = sample_event
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = sample_task
        mock_task_repository.save.side_effect = Exception('Database error')

        result = handler.handle_message_callback({'test': 'data'})

        assert result.success is False
        assert result.status == CallbackStatus.PROCESSING_ERROR


class TestHandleMessageCallbackWithVerification:
    """测试带签名验证的消息回调处理"""

    def test_handle_signature_invalid(self, handler, mock_callback_parser):
        """测试签名无效"""
        mock_callback_parser.verify_signature.return_value = False

        result = handler.handle_message_callback_with_verification(
            callback_data={'test': 'data'},
            timestamp='1234567890',
            nonce='nonce',
            signature='invalid',
        )

        assert result.success is False
        assert result.status == CallbackStatus.SIGNATURE_INVALID

    def test_handle_signature_valid(self, handler, mock_callback_parser, mock_task_repository, sample_event, sample_task):
        """测试签名有效"""
        mock_callback_parser.verify_signature.return_value = True
        mock_callback_parser.parse_message_event.return_value = sample_event
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = sample_task

        result = handler.handle_message_callback_with_verification(
            callback_data={'test': 'data'},
            timestamp='1234567890',
            nonce='nonce',
            signature='valid',
        )

        assert result.success is True


class TestMatchTaskByMessage:
    """测试根据消息匹配任务"""

    def test_match_by_harness_task_id(self, handler, mock_callback_parser, mock_task_repository, sample_task):
        """测试通过harness_task_id匹配"""
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = sample_task

        result = handler.match_task_by_message('确认 TASK-123')

        assert result == sample_task

    def test_match_by_id(self, handler, mock_callback_parser, mock_task_repository, sample_task):
        """测试通过id匹配"""
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = None
        mock_task_repository.find_by_id.return_value = sample_task

        result = handler.match_task_by_message('确认 TASK-123')

        assert result == sample_task

    def test_match_not_found(self, handler, mock_callback_parser, mock_task_repository):
        """测试未找到任务"""
        mock_callback_parser.extract_task_id_from_message.return_value = 'TASK-123'
        mock_task_repository.find_by_harness_task_id.return_value = None
        mock_task_repository.find_by_id.return_value = None

        result = handler.match_task_by_message('确认 TASK-123')

        assert result is None

    def test_match_no_task_id(self, handler, mock_callback_parser):
        """测试没有任务ID"""
        mock_callback_parser.extract_task_id_from_message.return_value = None

        result = handler.match_task_by_message('确认')

        assert result is None


class TestGetPendingReplyTasks:
    """测试获取等待回复的任务"""

    def test_get_pending_tasks(self, handler, mock_task_repository, sample_task):
        """测试获取等待回复的任务"""
        mock_task_repository.find_by_status.return_value = [sample_task]

        result = handler.get_pending_reply_tasks()

        assert len(result) == 1
        assert result[0] == sample_task
        mock_task_repository.find_by_status.assert_called_once_with(TaskStatus.SENT)


class TestCallbackResult:
    """测试回调结果"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = CallbackResult(
            success=True,
            message='Success',
            task_id='TASK-123',
            status=CallbackStatus.SUCCESS,
        )
        d = result.to_dict()
        assert d['success'] is True
        assert d['message'] == 'Success'
        assert d['task_id'] == 'TASK-123'
        assert d['status'] == 'success'
