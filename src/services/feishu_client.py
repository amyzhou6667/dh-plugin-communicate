"""
飞书开放平台客户端模块
"""
import json
import logging
import time
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FeishuAuthError(Exception):
    """飞书认证错误"""
    pass


class FeishuAPIError(Exception):
    """飞书 API 错误"""
    pass


class FeishuClient:
    """飞书开放平台客户端"""

    BASE_URL = 'https://open.feishu.cn/open-apis'

    def __init__(self, app_id: str, app_secret: str):
        """初始化飞书客户端

        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.timeout = 30

        # 令牌缓存
        self._tenant_access_token = None
        self._token_expire_time = 0

    def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token

        Returns:
            str: 访问令牌

        Raises:
            FeishuAuthError: 认证失败
        """
        # 检查缓存是否有效
        if self._tenant_access_token and time.time() < self._token_expire_time:
            return self._tenant_access_token

        url = f'{self.BASE_URL}/auth/v3/tenant_access_token/internal'
        json_data = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }

        try:
            response = requests.post(url, json=json_data, timeout=self.timeout)
        except requests.ConnectionError as e:
            logger.error(f'Connection error when getting tenant access token: {e}')
            raise FeishuAuthError(f'Connection error: {e}')
        except requests.Timeout as e:
            logger.error(f'Timeout when getting tenant access token: {e}')
            raise FeishuAuthError(f'Request timeout: {e}')

        data = response.json()

        if data.get('code') != 0:
            logger.error(f'Failed to get tenant access token: {data}')
            raise FeishuAuthError(f'Auth failed: {data.get("msg", "Unknown error")}')

        self._tenant_access_token = data['tenant_access_token']
        # 提前5分钟过期，避免边界情况
        self._token_expire_time = time.time() + data.get('expire', 7200) - 300

        logger.info('Successfully obtained tenant access token')
        return self._tenant_access_token

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头
        """
        token = self.get_tenant_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _send_message(self, open_id: str, msg_type: str, content: str) -> str:
        """发送消息的公共方法

        Args:
            open_id: 接收者的 open_id
            msg_type: 消息类型 (text, interactive)
            content: 消息内容（JSON字符串）

        Returns:
            str: 消息ID

        Raises:
            FeishuAuthError: 认证失败
            FeishuAPIError: API调用失败
        """
        url = f'{self.BASE_URL}/im/v1/messages?receive_id_type=open_id'
        json_data = {
            'receive_id': open_id,
            'msg_type': msg_type,
            'content': content
        }

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=json_data,
                timeout=self.timeout
            )
        except requests.ConnectionError as e:
            logger.error(f'Connection error when sending {msg_type} message: {e}')
            raise FeishuAPIError(f'Connection error: {e}')
        except requests.Timeout as e:
            logger.error(f'Timeout when sending {msg_type} message: {e}')
            raise FeishuAPIError(f'Request timeout: {e}')

        data = response.json()

        if data.get('code') != 0:
            logger.error(f'Failed to send {msg_type} message: {data}')
            raise FeishuAPIError(f'API error: {data.get("msg", "Unknown error")}')

        message_id = data['data']['message_id']
        logger.info(f'Successfully sent {msg_type} message to {open_id}, message_id: {message_id}')
        return message_id

    def send_text_message(self, open_id: str, text: str) -> str:
        """发送文本消息

        Args:
            open_id: 接收者的 open_id
            text: 消息文本

        Returns:
            str: 消息ID

        Raises:
            FeishuAuthError: 认证失败
            FeishuAPIError: API调用失败
        """
        content = json.dumps({'text': text})
        return self._send_message(open_id, 'text', content)

    def send_card_message(self, open_id: str, card: dict) -> str:
        """发送卡片消息

        Args:
            open_id: 接收者的 open_id
            card: 卡片内容

        Returns:
            str: 消息ID

        Raises:
            FeishuAuthError: 认证失败
            FeishuAPIError: API调用失败
        """
        content = json.dumps(card)
        return self._send_message(open_id, 'interactive', content)
