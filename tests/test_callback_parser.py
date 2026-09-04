"""飞书回调解析器测试"""

import pytest
from src.services.callback_parser import FeishuCallbackParser, FeishuMessageEvent


@pytest.fixture
def parser():
    """创建回调解析器实例"""
    return FeishuCallbackParser(
        encrypt_key='test_encrypt_key',
        verification_token='test_token',
    )


@pytest.fixture
def sample_callback_data():
    """示例回调数据"""
    return {
        'schema': '2.0',
        'header': {
            'event_id': 'evt_123',
            'event_type': 'im.message.receive_v1',
            'create_time': '1234567890',
            'token': 'test_token',
            'app_id': 'cli_test',
            'tenant_key': 'tenant_123',
        },
        'event': {
            'sender': {
                'sender_id': {
                    'union_id': 'on_union',
                    'user_id': 'user_123',
                    'open_id': 'ou_open_id',
                },
                'sender_type': 'user',
                'tenant_key': 'tenant_123',
            },
            'message': {
                'message_id': 'msg_123',
                'root_id': '',
                'parent_id': '',
                'create_time': '1234567890',
                'chat_id': 'chat_123',
                'chat_type': 'p2p',
                'message_type': 'text',
                'content': '{"text":"确认 TASK-123"}',
                'mentions': [],
            },
        },
    }


class TestParseMessageEvent:
    """测试解析消息事件"""

    def test_parse_success(self, parser, sample_callback_data):
        """测试解析成功"""
        event = parser.parse_message_event(sample_callback_data)

        assert event is not None
        assert isinstance(event, FeishuMessageEvent)
        assert event.message_id == 'msg_123'
        assert event.chat_id == 'chat_123'
        assert event.chat_type == 'p2p'
        assert event.message_type == 'text'
        assert event.content == '确认 TASK-123'
        assert event.sender_open_id == 'ou_open_id'

    def test_parse_invalid_type(self, parser):
        """测试解析无效数据类型"""
        event = parser.parse_message_event('invalid')
        assert event is None

    def test_parse_wrong_event_type(self, parser, sample_callback_data):
        """测试解析错误的事件类型"""
        sample_callback_data['header']['event_type'] = 'im.chat.updated'
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_missing_event(self, parser, sample_callback_data):
        """测试缺少事件数据"""
        del sample_callback_data['event']
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_missing_message(self, parser, sample_callback_data):
        """测试缺少消息数据"""
        del sample_callback_data['event']['message']
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_missing_sender(self, parser, sample_callback_data):
        """测试缺少发送者信息"""
        del sample_callback_data['event']['sender']['sender_id']['open_id']
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_missing_message_id(self, parser, sample_callback_data):
        """测试缺少消息ID"""
        del sample_callback_data['event']['message']['message_id']
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_invalid_content_json(self, parser, sample_callback_data):
        """测试无效的消息内容JSON"""
        sample_callback_data['event']['message']['content'] = 'invalid json'
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_post_message(self, parser, sample_callback_data):
        """测试解析富文本消息"""
        sample_callback_data['event']['message']['message_type'] = 'post'
        sample_callback_data['event']['message']['content'] = '{"content":[[{"tag":"text","text":"确认 TASK-123"}]]}'
        event = parser.parse_message_event(sample_callback_data)

        assert event is not None
        assert event.message_type == 'post'
        assert '确认 TASK-123' in event.content

    def test_parse_post_message_empty(self, parser, sample_callback_data):
        """测试解析空富文本消息"""
        sample_callback_data['event']['message']['message_type'] = 'post'
        sample_callback_data['event']['message']['content'] = '{"content":[]}'
        event = parser.parse_message_event(sample_callback_data)
        assert event is None

    def test_parse_unsupported_message_type(self, parser, sample_callback_data):
        """测试解析不支持的消息类型"""
        sample_callback_data['event']['message']['message_type'] = 'image'
        event = parser.parse_message_event(sample_callback_data)
        assert event is None


class TestVerifySignature:
    """测试验证签名"""

    def test_verify_success(self, parser):
        """测试签名验证成功"""
        import hashlib
        timestamp = '1234567890'
        nonce = 'test_nonce'
        body = '{"test":"data"}'
        sign_str = f"{timestamp}{nonce}{parser.encrypt_key}{body}"
        expected_signature = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()

        result = parser.verify_signature(timestamp, nonce, body, expected_signature)
        assert result is True

    def test_verify_failure(self, parser):
        """测试签名验证失败"""
        result = parser.verify_signature('1234567890', 'nonce', 'body', 'invalid_signature')
        assert result is False

    def test_verify_no_encrypt_key(self):
        """测试没有加密密钥时跳过验证"""
        parser = FeishuCallbackParser(encrypt_key=None)
        result = parser.verify_signature('1234567890', 'nonce', 'body', 'any_signature')
        assert result is True


class TestExtractTaskId:
    """测试提取任务ID"""

    def test_extract_task_id_basic(self, parser):
        """测试提取基本任务ID"""
        assert parser.extract_task_id_from_message('确认 TASK-123') == 'TASK-123'
        assert parser.extract_task_id_from_message('TASK-123 确认') == 'TASK-123'

    def test_extract_task_id_with_colon(self, parser):
        """测试带冒号的任务ID"""
        assert parser.extract_task_id_from_message('确认:TASK-123') == 'TASK-123'

    def test_extract_task_id_underscore(self, parser):
        """测试带下划线的任务ID"""
        assert parser.extract_task_id_from_message('确认 TASK_123') == 'TASK_123'

    def test_extract_task_id_lowercase(self, parser):
        """测试小写任务ID"""
        assert parser.extract_task_id_from_message('确认 task-123') == 'task-123'

    def test_extract_task_id_only(self, parser):
        """测试只有任务ID"""
        assert parser.extract_task_id_from_message('TASK-123') == 'TASK-123'

    def test_extract_task_id_not_found(self, parser):
        """测试未找到任务ID"""
        assert parser.extract_task_id_from_message('确认') is None
        assert parser.extract_task_id_from_message('同意执行') is None

    def test_extract_task_id_empty(self, parser):
        """测试空消息"""
        assert parser.extract_task_id_from_message('') is None
        assert parser.extract_task_id_from_message(None) is None


class TestIsConfirmationMessage:
    """测试判断确认消息"""

    def test_confirm_keywords(self, parser):
        """测试确认关键词"""
        assert parser.is_confirmation_message('确认') is True
        assert parser.is_confirmation_message('同意') is True
        assert parser.is_confirmation_message('通过') is True
        assert parser.is_confirmation_message('approve') is True
        assert parser.is_confirmation_message('confirm') is True
        assert parser.is_confirmation_message('yes') is True
        assert parser.is_confirmation_message('ok') is True

    def test_reject_keywords(self, parser):
        """测试拒绝关键词"""
        assert parser.is_confirmation_message('拒绝') is True
        assert parser.is_confirmation_message('否决') is True
        assert parser.is_confirmation_message('不通过') is True
        assert parser.is_confirmation_message('reject') is True
        assert parser.is_confirmation_message('deny') is True
        assert parser.is_confirmation_message('no') is True

    def test_normal_message(self, parser):
        """测试普通消息"""
        assert parser.is_confirmation_message('你好') is False
        assert parser.is_confirmation_message('请问进度如何？') is False

    def test_empty_message(self, parser):
        """测试空消息"""
        assert parser.is_confirmation_message('') is False
        assert parser.is_confirmation_message(None) is False


class TestFeishuMessageEvent:
    """测试消息事件对象"""

    def test_to_dict(self):
        """测试转换为字典"""
        event = FeishuMessageEvent(
            message_id='msg_123',
            chat_id='chat_123',
            chat_type='p2p',
            message_type='text',
            content='确认',
            sender_open_id='ou_123',
            create_time='1234567890',
        )
        result = event.to_dict()
        assert result['message_id'] == 'msg_123'
        assert result['content'] == '确认'
        assert result['sender_open_id'] == 'ou_123'
