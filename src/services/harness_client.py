"""
DeepSeek Harness 客户端模块
"""
import logging
import requests
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class HarnessConnectionError(Exception):
    """Harness 连接错误"""
    pass


class HarnessAPIError(Exception):
    """Harness API 错误"""
    pass


class HarnessClient:
    """DeepSeek Harness 客户端"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """初始化客户端

        Args:
            base_url: DeepSeek Harness 基础URL
            api_key: API密钥（可选）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = 30

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头

        Returns:
            Dict[str, str]: 请求头
        """
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def get_pending_tasks(self) -> List[dict]:
        """获取待确认任务列表

        Returns:
            List[dict]: 任务列表，每个任务包含 id, content, context 等字段

        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
        url = f'{self.base_url}/api/tasks/pending'

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
        except requests.ConnectionError as e:
            logger.error(f'Connection refused when getting pending tasks: {e}')
            raise HarnessConnectionError(f'Connection refused: {e}')
        except requests.Timeout as e:
            logger.error(f'Timeout when getting pending tasks: {e}')
            raise HarnessConnectionError(f'Request timed out: {e}')

        if response.status_code != 200:
            logger.error(f'Failed to get pending tasks: {response.status_code} - {response.text}')
            raise HarnessAPIError(
                f'API error: {response.status_code} - {response.text}'
            )

        data = response.json()
        tasks = data.get('tasks', [])
        logger.info(f'Retrieved {len(tasks)} pending tasks from Harness')
        return tasks

    def submit_reply(self, task_id: str, reply_text: str, user_id: str) -> bool:
        """提交用户回复到 DeepSeek Harness

        Args:
            task_id: 任务ID
            reply_text: 回复文本
            user_id: 用户ID

        Returns:
            bool: 提交是否成功

        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
        url = f'{self.base_url}/api/tasks/{task_id}/reply'
        headers = {
            'Content-Type': 'application/json',
            **self._get_headers()
        }
        json_data = {
            'reply_text': reply_text,
            'user_id': user_id
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=json_data,
                timeout=self.timeout
            )
        except requests.ConnectionError as e:
            logger.error(f'Connection refused when submitting reply for task {task_id}: {e}')
            raise HarnessConnectionError(f'Connection refused: {e}')
        except requests.Timeout as e:
            logger.error(f'Timeout when submitting reply for task {task_id}: {e}')
            raise HarnessConnectionError(f'Request timed out: {e}')

        if response.status_code != 200:
            logger.error(f'Failed to submit reply for task {task_id}: {response.status_code} - {response.text}')
            raise HarnessAPIError(
                f'API error: {response.status_code} - {response.text}'
            )

        logger.info(f'Successfully submitted reply for task {task_id}')
        return True

    def health_check(self) -> bool:
        """健康检查

        Returns:
            bool: 服务是否健康
        """
        url = f'{self.base_url}/health'

        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False
