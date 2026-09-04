"""
飞书客户端测试
基于接口签名契约设计测试用例
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests


class TestFeishuClient:
    """FeishuClient 测试"""

    def test_initialization(self):
        """测试飞书客户端初始化"""
        from src.services.feishu_client import FeishuClient

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )
        assert client.app_id == 'cli_test123'
        assert client.app_secret == 'test_secret'

    @patch('src.services.feishu_client.requests.post')
    def test_get_tenant_access_token_success(self, mock_post):
        """测试获取 tenant_access_token 成功"""
        from src.services.feishu_client import FeishuClient

        # Mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'tenant_access_token': 't-test_token_123',
            'expire': 7200
        }
        mock_post.return_value = mock_response

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )
        token = client.get_tenant_access_token()

        assert token == 't-test_token_123'
        mock_post.assert_called_once_with(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            json={'app_id': 'cli_test123', 'app_secret': 'test_secret'},
            timeout=30
        )

    @patch('src.services.feishu_client.requests.post')
    def test_get_tenant_access_token_failure(self, mock_post):
        """测试获取 tenant_access_token 失败"""
        from src.services.feishu_client import FeishuClient, FeishuAuthError

        # Mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 10003,
            'msg': 'invalid app_id'
        }
        mock_post.return_value = mock_response

        client = FeishuClient(
            app_id='cli_invalid',
            app_secret='test_secret'
        )

        with pytest.raises(FeishuAuthError):
            client.get_tenant_access_token()

    @patch('src.services.feishu_client.requests.post')
    def test_get_tenant_access_token_connection_error(self, mock_post):
        """测试获取 tenant_access_token 连接失败"""
        from src.services.feishu_client import FeishuClient, FeishuAuthError

        mock_post.side_effect = requests.ConnectionError('Connection refused')

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )

        with pytest.raises(FeishuAuthError):
            client.get_tenant_access_token()

    @patch('src.services.feishu_client.requests.post')
    def test_send_text_message_success(self, mock_post):
        """测试发送文本消息成功"""
        from src.services.feishu_client import FeishuClient

        # Mock 获取令牌的响应
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'tenant_access_token': 't-test_token_123',
            'expire': 7200
        }

        # Mock 发送消息的响应
        mock_send_response = Mock()
        mock_send_response.status_code = 200
        mock_send_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'data': {
                'message_id': 'om_test_msg_123',
                'msg_type': 'text'
            }
        }

        # 设置 mock 返回值
        mock_post.side_effect = [mock_token_response, mock_send_response]

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )
        message_id = client.send_text_message(
            open_id='ou_test_user_123',
            text='请确认操作'
        )

        assert message_id == 'om_test_msg_123'
        assert mock_post.call_count == 2

    @patch('src.services.feishu_client.requests.post')
    def test_send_text_message_failure(self, mock_post):
        """测试发送文本消息失败"""
        from src.services.feishu_client import FeishuClient, FeishuAPIError

        # Mock 获取令牌的响应
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'tenant_access_token': 't-test_token_123',
            'expire': 7200
        }

        # Mock 发送消息的响应（失败）
        mock_send_response = Mock()
        mock_send_response.status_code = 200
        mock_send_response.json.return_value = {
            'code': 230001,
            'msg': 'invalid receive_id'
        }

        mock_post.side_effect = [mock_token_response, mock_send_response]

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )

        with pytest.raises(FeishuAPIError):
            client.send_text_message(
                open_id='ou_invalid',
                text='请确认操作'
            )

    @patch('src.services.feishu_client.requests.post')
    def test_send_card_message_success(self, mock_post):
        """测试发送卡片消息成功"""
        from src.services.feishu_client import FeishuClient

        # Mock 获取令牌的响应
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'tenant_access_token': 't-test_token_123',
            'expire': 7200
        }

        # Mock 发送消息的响应
        mock_send_response = Mock()
        mock_send_response.status_code = 200
        mock_send_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'data': {
                'message_id': 'om_test_card_123',
                'msg_type': 'interactive'
            }
        }

        mock_post.side_effect = [mock_token_response, mock_send_response]

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )

        card = {
            'config': {'wide_screen_mode': True},
            'header': {
                'title': {'tag': 'plain_text', 'content': '确认请求'}
            },
            'elements': [
                {
                    'tag': 'div',
                    'text': {'tag': 'lark_md', 'content': '请确认操作'}
                }
            ]
        }

        message_id = client.send_card_message(
            open_id='ou_test_user_123',
            card=card
        )

        assert message_id == 'om_test_card_123'

    @patch('src.services.feishu_client.requests.post')
    def test_send_card_message_failure(self, mock_post):
        """测试发送卡片消息失败"""
        from src.services.feishu_client import FeishuClient, FeishuAPIError

        # Mock 获取令牌的响应
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'tenant_access_token': 't-test_token_123',
            'expire': 7200
        }

        # Mock 发送消息的响应（失败）
        mock_send_response = Mock()
        mock_send_response.status_code = 200
        mock_send_response.json.return_value = {
            'code': 230001,
            'msg': 'invalid receive_id'
        }

        mock_post.side_effect = [mock_token_response, mock_send_response]

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )

        card = {'test': 'card'}

        with pytest.raises(FeishuAPIError):
            client.send_card_message(
                open_id='ou_invalid',
                card=card
            )

    @patch('src.services.feishu_client.requests.post')
    def test_token_cache(self, mock_post):
        """测试令牌缓存"""
        from src.services.feishu_client import FeishuClient

        # Mock 获取令牌的响应
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'code': 0,
            'msg': 'ok',
            'tenant_access_token': 't-test_token_123',
            'expire': 7200
        }
        mock_post.return_value = mock_token_response

        client = FeishuClient(
            app_id='cli_test123',
            app_secret='test_secret'
        )

        # 第一次获取令牌
        token1 = client.get_tenant_access_token()
        assert token1 == 't-test_token_123'

        # 第二次获取令牌（应该使用缓存）
        token2 = client.get_tenant_access_token()
        assert token2 == 't-test_token_123'

        # 验证只调用了一次API
        assert mock_post.call_count == 1


class TestFeishuMessageFormatter:
    """FeishuMessageFormatter 测试"""

    def test_format_confirmation_card(self):
        """测试格式化确认卡片"""
        from src.services.feishu_message_formatter import FeishuMessageFormatter

        card = FeishuMessageFormatter.format_confirmation_card(
            task_id='task_123',
            content='请确认删除用户数据',
            context={'user_id': 'user_789'}
        )

        assert card['config']['wide_screen_mode'] is True
        assert card['header']['title']['content'] == '确认请求'
        assert len(card['elements']) == 4

        # 验证包含任务内容
        div_element = card['elements'][0]
        assert div_element['tag'] == 'div'
        assert '请确认删除用户数据' in div_element['text']['content']

        # 验证包含分隔线
        hr_element = card['elements'][1]
        assert hr_element['tag'] == 'hr'

        # 验证包含备注
        note_element = card['elements'][2]
        assert note_element['tag'] == 'note'
        assert 'task_123' in note_element['elements'][0]['content']

        # 验证包含按钮
        action_element = card['elements'][3]
        assert action_element['tag'] == 'action'
        assert len(action_element['actions']) == 2

    def test_format_confirmation_card_without_context(self):
        """测试格式化确认卡片（无上下文）"""
        from src.services.feishu_message_formatter import FeishuMessageFormatter

        card = FeishuMessageFormatter.format_confirmation_card(
            task_id='task_123',
            content='请确认操作'
        )

        assert card['config']['wide_screen_mode'] is True
        assert card['header']['title']['content'] == '确认请求'

    def test_format_text_message(self):
        """测试格式化文本消息"""
        from src.services.feishu_message_formatter import FeishuMessageFormatter

        text = FeishuMessageFormatter.format_text_message('请确认操作')
        assert text == '请确认操作'

    def test_format_text_message_with_context(self):
        """测试格式化文本消息（带上下文）"""
        from src.services.feishu_message_formatter import FeishuMessageFormatter

        text = FeishuMessageFormatter.format_text_message(
            '请确认操作',
            context={'action': 'delete'}
        )
        assert '请确认操作' in text
        assert 'delete' in text
