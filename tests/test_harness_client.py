"""
DeepSeek Harness 客户端测试
基于接口签名契约设计测试用例
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests


class TestHarnessClient:
    """HarnessClient 测试"""

    def test_initialization(self):
        """测试客户端初始化"""
        from src.services.harness_client import HarnessClient

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        assert client.base_url == 'http://127.0.0.1:3080'
        assert client.api_key is None

    def test_initialization_with_api_key(self):
        """测试客户端初始化（带API密钥）"""
        from src.services.harness_client import HarnessClient

        client = HarnessClient(
            base_url='http://127.0.0.1:3080',
            api_key='test_api_key'
        )
        assert client.base_url == 'http://127.0.0.1:3080'
        assert client.api_key == 'test_api_key'

    @patch('src.services.harness_client.requests.get')
    def test_get_pending_tasks_success(self, mock_get):
        """测试获取待确认任务成功"""
        from src.services.harness_client import HarnessClient

        # Mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tasks': [
                {
                    'id': 'task_1',
                    'content': '请确认操作',
                    'context': {'action': 'delete'}
                },
                {
                    'id': 'task_2',
                    'content': '请确认部署',
                    'context': {'env': 'production'}
                }
            ]
        }
        mock_get.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        tasks = client.get_pending_tasks()

        assert len(tasks) == 2
        assert tasks[0]['id'] == 'task_1'
        assert tasks[1]['id'] == 'task_2'
        mock_get.assert_called_once_with(
            'http://127.0.0.1:3080/api/tasks/pending',
            headers={},
            timeout=30
        )

    @patch('src.services.harness_client.requests.get')
    def test_get_pending_tasks_empty(self, mock_get):
        """测试获取待确认任务（空列表）"""
        from src.services.harness_client import HarnessClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'tasks': []}
        mock_get.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        tasks = client.get_pending_tasks()

        assert len(tasks) == 0

    @patch('src.services.harness_client.requests.get')
    def test_get_pending_tasks_connection_error(self, mock_get):
        """测试获取待确认任务：连接失败"""
        from src.services.harness_client import HarnessClient, HarnessConnectionError

        mock_get.side_effect = requests.ConnectionError('Connection refused')

        client = HarnessClient(base_url='http://127.0.0.1:3080')

        with pytest.raises(HarnessConnectionError):
            client.get_pending_tasks()

    @patch('src.services.harness_client.requests.get')
    def test_get_pending_tasks_timeout(self, mock_get):
        """测试获取待确认任务：超时"""
        from src.services.harness_client import HarnessClient, HarnessConnectionError

        mock_get.side_effect = requests.Timeout('Request timed out')

        client = HarnessClient(base_url='http://127.0.0.1:3080')

        with pytest.raises(HarnessConnectionError):
            client.get_pending_tasks()

    @patch('src.services.harness_client.requests.get')
    def test_get_pending_tasks_api_error(self, mock_get):
        """测试获取待确认任务：API错误"""
        from src.services.harness_client import HarnessClient, HarnessAPIError

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')

        with pytest.raises(HarnessAPIError):
            client.get_pending_tasks()

    @patch('src.services.harness_client.requests.get')
    def test_get_pending_tasks_with_api_key(self, mock_get):
        """测试获取待确认任务（带API密钥）"""
        from src.services.harness_client import HarnessClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'tasks': []}
        mock_get.return_value = mock_response

        client = HarnessClient(
            base_url='http://127.0.0.1:3080',
            api_key='test_api_key'
        )
        client.get_pending_tasks()

        mock_get.assert_called_once_with(
            'http://127.0.0.1:3080/api/tasks/pending',
            headers={'Authorization': 'Bearer test_api_key'},
            timeout=30
        )

    @patch('src.services.harness_client.requests.post')
    def test_submit_reply_success(self, mock_post):
        """测试提交回复成功"""
        from src.services.harness_client import HarnessClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        result = client.submit_reply(
            task_id='task_123',
            reply_text='确认执行',
            user_id='user_456'
        )

        assert result is True
        mock_post.assert_called_once_with(
            'http://127.0.0.1:3080/api/tasks/task_123/reply',
            headers={'Content-Type': 'application/json'},
            json={'reply_text': '确认执行', 'user_id': 'user_456'},
            timeout=30
        )

    @patch('src.services.harness_client.requests.post')
    def test_submit_reply_failure(self, mock_post):
        """测试提交回复失败"""
        from src.services.harness_client import HarnessClient, HarnessAPIError

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')

        with pytest.raises(HarnessAPIError):
            client.submit_reply(
                task_id='task_123',
                reply_text='确认执行',
                user_id='user_456'
            )

    @patch('src.services.harness_client.requests.post')
    def test_submit_reply_connection_error(self, mock_post):
        """测试提交回复：连接失败"""
        from src.services.harness_client import HarnessClient, HarnessConnectionError

        mock_post.side_effect = requests.ConnectionError('Connection refused')

        client = HarnessClient(base_url='http://127.0.0.1:3080')

        with pytest.raises(HarnessConnectionError):
            client.submit_reply(
                task_id='task_123',
                reply_text='确认执行',
                user_id='user_456'
            )

    @patch('src.services.harness_client.requests.get')
    def test_health_check_success(self, mock_get):
        """测试健康检查成功"""
        from src.services.harness_client import HarnessClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        result = client.health_check()

        assert result is True
        mock_get.assert_called_once_with(
            'http://127.0.0.1:3080/health',
            headers={},
            timeout=10
        )

    @patch('src.services.harness_client.requests.get')
    def test_health_check_failure(self, mock_get):
        """测试健康检查失败"""
        from src.services.harness_client import HarnessClient

        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        result = client.health_check()

        assert result is False

    @patch('src.services.harness_client.requests.get')
    def test_health_check_connection_error(self, mock_get):
        """测试健康检查：连接失败"""
        from src.services.harness_client import HarnessClient

        mock_get.side_effect = requests.ConnectionError('Connection refused')

        client = HarnessClient(base_url='http://127.0.0.1:3080')
        result = client.health_check()

        assert result is False
