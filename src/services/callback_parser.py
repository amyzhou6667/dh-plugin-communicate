"""飞书回调解析器模块

负责解析飞书回调数据、验证签名、提取任务ID。
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FeishuMessageEvent:
    """飞书消息事件"""

    message_id: str
    chat_id: str
    chat_type: str
    message_type: str
    content: str
    sender_open_id: str
    create_time: str

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'chat_id': self.chat_id,
            'chat_type': self.chat_type,
            'message_type': self.message_type,
            'content': self.content,
            'sender_open_id': self.sender_open_id,
            'create_time': self.create_time,
        }


class FeishuCallbackParser:
    """飞书回调解析器"""

    def __init__(self, encrypt_key: Optional[str] = None, verification_token: Optional[str] = None):
        """初始化回调解析器

        Args:
            encrypt_key: 加密密钥（可选）
            verification_token: 验证令牌（可选）
        """
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token

    def parse_message_event(self, callback_data: dict) -> Optional[FeishuMessageEvent]:
        """解析消息事件

        Args:
            callback_data: 飞书回调数据

        Returns:
            Optional[FeishuMessageEvent]: 消息事件对象，解析失败返回None
        """
        if not isinstance(callback_data, dict):
            logger.warning("Invalid callback data type: %s", type(callback_data))
            return None

        # 验证事件类型
        header = callback_data.get('header', {})
        event_type = header.get('event_type')
        if event_type != 'im.message.receive_v1':
            logger.debug("Ignoring event type: %s", event_type)
            return None

        # 提取事件数据
        event = callback_data.get('event', {})
        if not event:
            logger.warning("No event data in callback")
            return None

        # 提取消息信息
        message = event.get('message', {})
        if not message:
            logger.warning("No message data in event")
            return None

        # 提取发送者信息
        sender = event.get('sender', {})
        sender_id = sender.get('sender_id', {})
        sender_open_id = sender_id.get('open_id')

        if not sender_open_id:
            logger.warning("No sender open_id in event")
            return None

        # 提取消息内容
        message_id = message.get('message_id')
        chat_id = message.get('chat_id')
        chat_type = message.get('chat_type')
        message_type = message.get('message_type')
        content_str = message.get('content')
        create_time = message.get('create_time')

        if not all([message_id, chat_id, chat_type, message_type, content_str]):
            logger.warning("Missing required message fields")
            return None

        # 解析消息内容
        content = self._parse_message_content(content_str, message_type)
        if content is None:
            return None

        return FeishuMessageEvent(
            message_id=message_id,
            chat_id=chat_id,
            chat_type=chat_type,
            message_type=message_type,
            content=content,
            sender_open_id=sender_open_id,
            create_time=create_time or '',
        )

    def _parse_message_content(self, content_str: str, message_type: str) -> Optional[str]:
        """解析消息内容

        Args:
            content_str: JSON格式的消息内容字符串
            message_type: 消息类型

        Returns:
            Optional[str]: 解析后的消息文本，失败返回None
        """
        try:
            content_json = json.loads(content_str)
        except json.JSONDecodeError:
            logger.warning("Invalid message content JSON format")
            return None

        if message_type == 'text':
            return content_json.get('text')
        elif message_type == 'post':
            # 富文本消息，提取纯文本
            return self._extract_post_text(content_json)
        else:
            logger.debug("Unsupported message type: %s", message_type)
            return None

    def _extract_post_text(self, post_content: dict) -> Optional[str]:
        """从富文本消息中提取纯文本

        Args:
            post_content: 富文本内容

        Returns:
            Optional[str]: 提取的纯文本
        """
        try:
            texts = []
            content = post_content.get('content', [])
            for paragraph in content:
                if isinstance(paragraph, list):
                    for element in paragraph:
                        if isinstance(element, dict) and element.get('tag') == 'text':
                            texts.append(element.get('text', ''))
            return ''.join(texts) if texts else None
        except Exception as e:
            logger.error("Failed to extract post text: %s", e)
            return None

    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str) -> bool:
        """验证回调签名

        飞书签名算法：sha256(timestamp + nonce + encrypt_key + body)

        Args:
            timestamp: 时间戳
            nonce: 随机数
            body: 请求体
            signature: 签名

        Returns:
            bool: 签名是否有效
        """
        if not self.encrypt_key:
            logger.warning("No encrypt key configured, signature verification is disabled. "
                           "Please configure encrypt_key for production use.")
            return True

        # 计算签名
        sign_str = f"{timestamp}{nonce}{self.encrypt_key}{body}"
        calculated_signature = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()

        return calculated_signature == signature

    def extract_task_id_from_message(self, message_content: str) -> Optional[str]:
        """从消息内容中提取任务ID

        支持格式：
        - "确认 TASK-123"
        - "确认:TASK-123"
        - "TASK-123 确认"
        - 纯任务ID

        Args:
            message_content: 消息内容

        Returns:
            Optional[str]: 任务ID，提取失败返回None
        """
        if not message_content:
            return None

        # 清理消息内容
        content = message_content.strip()

        # 匹配任务ID模式
        # 常见格式：TASK-123, task-abc, TASK_456, task-123 等
        pattern = r'(task[-_]\w+)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def is_confirmation_message(self, message_content: str) -> bool:
        """判断消息是否是确认消息

        Args:
            message_content: 消息内容

        Returns:
            bool: 是否是确认消息
        """
        if not message_content:
            return False

        content = message_content.strip().lower()

        # 确认关键词
        confirm_keywords = ['确认', '同意', '通过', 'approve', 'confirm', 'yes', 'ok']
        reject_keywords = ['拒绝', '否决', '不通过', 'reject', 'deny', 'no']

        # 检查是否包含确认关键词
        for keyword in confirm_keywords:
            if keyword in content:
                return True

        # 检查是否包含拒绝关键词（也属于回复）
        for keyword in reject_keywords:
            if keyword in content:
                return True

        return False
