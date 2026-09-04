"""回调处理器模块

负责处理飞书回调消息，匹配任务并更新状态。
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from src.models.task import Task, TaskStatus, db
from src.repositories.task_repository import TaskRepository
from src.services.callback_parser import FeishuCallbackParser, FeishuMessageEvent
from src.services.harness_client import HarnessClient

logger = logging.getLogger(__name__)


class CallbackStatus(Enum):
    """回调处理状态"""
    SUCCESS = 'success'
    TASK_NOT_FOUND = 'task_not_found'
    INVALID_DATA = 'invalid_data'
    PROCESSING_ERROR = 'processing_error'
    SIGNATURE_INVALID = 'signature_invalid'


@dataclass
class CallbackResult:
    """回调处理结果"""

    success: bool
    message: str
    task_id: Optional[str] = None
    status: CallbackStatus = CallbackStatus.SUCCESS

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'success': self.success,
            'message': self.message,
            'task_id': self.task_id,
            'status': self.status.value,
        }


class CallbackHandler:
    """回调处理器"""

    def __init__(self, callback_parser: FeishuCallbackParser,
                 task_repository: TaskRepository,
                 harness_client: HarnessClient):
        """初始化回调处理器

        Args:
            callback_parser: 飞书回调解析器
            task_repository: 任务仓库
            harness_client: Harness客户端
        """
        self.callback_parser = callback_parser
        self.task_repository = task_repository
        self.harness_client = harness_client

    def handle_message_callback(self, callback_data: dict) -> CallbackResult:
        """处理消息回调

        Args:
            callback_data: 飞书回调数据

        Returns:
            CallbackResult: 处理结果
        """
        # 解析消息事件
        event = self.callback_parser.parse_message_event(callback_data)
        if not event:
            return CallbackResult(
                success=False,
                message="Failed to parse message event",
                status=CallbackStatus.INVALID_DATA,
            )

        # 处理消息
        return self._process_message_event(event)

    def handle_message_callback_with_verification(
        self,
        callback_data: dict,
        timestamp: str,
        nonce: str,
        signature: str,
    ) -> CallbackResult:
        """处理带签名验证的消息回调

        Args:
            callback_data: 飞书回调数据
            timestamp: 时间戳
            nonce: 随机数
            signature: 签名

        Returns:
            CallbackResult: 处理结果
        """
        # 验证签名
        body = json.dumps(callback_data, ensure_ascii=False)
        if not self.callback_parser.verify_signature(timestamp, nonce, body, signature):
            return CallbackResult(
                success=False,
                message="Invalid signature",
                status=CallbackStatus.SIGNATURE_INVALID,
            )

        # 解析消息事件
        event = self.callback_parser.parse_message_event(callback_data)
        if not event:
            return CallbackResult(
                success=False,
                message="Failed to parse message event",
                status=CallbackStatus.INVALID_DATA,
            )

        # 处理消息
        return self._process_message_event(event)

    def _process_message_event(self, event: FeishuMessageEvent) -> CallbackResult:
        """处理消息事件

        Args:
            event: 消息事件

        Returns:
            CallbackResult: 处理结果
        """
        # 提取任务ID
        task_id = self.callback_parser.extract_task_id_from_message(event.content)
        if not task_id:
            return CallbackResult(
                success=False,
                message="No task ID found in message",
                status=CallbackStatus.TASK_NOT_FOUND,
            )

        # 查找任务
        task = self.task_repository.find_by_harness_task_id(task_id)
        if not task:
            # 尝试直接查找
            task = self.task_repository.find_by_id(task_id)

        if not task:
            logger.warning("Task not found: %s", task_id)
            return CallbackResult(
                success=False,
                message=f"Task not found: {task_id}",
                task_id=task_id,
                status=CallbackStatus.TASK_NOT_FOUND,
            )

        # 更新任务状态
        return self._update_task_with_reply(task, event.content, event.sender_open_id)

    def _update_task_with_reply(self, task: Task, reply_content: str, user_id: str) -> CallbackResult:
        """更新任务回复

        Args:
            task: 任务对象
            reply_content: 回复内容
            user_id: 用户ID

        Returns:
            CallbackResult: 处理结果
        """
        try:
            # 更新任务状态
            task.status = TaskStatus.REPLIED
            task.user_reply = reply_content
            task.user_id = user_id

            # 保存到数据库
            self.task_repository.save(task)

            logger.info("Task %s updated with reply from user %s", task.id, user_id)

            return CallbackResult(
                success=True,
                message="Task reply received successfully",
                task_id=task.harness_task_id,
                status=CallbackStatus.SUCCESS,
            )

        except Exception as e:
            logger.error("Failed to update task %s: %s", task.id, e)
            return CallbackResult(
                success=False,
                message=f"Failed to update task: {str(e)}",
                task_id=task.harness_task_id,
                status=CallbackStatus.PROCESSING_ERROR,
            )

    def match_task_by_message(self, message_content: str) -> Optional[Task]:
        """根据消息匹配任务

        Args:
            message_content: 消息内容

        Returns:
            Optional[Task]: 匹配的任务，未找到返回None
        """
        # 提取任务ID
        task_id = self.callback_parser.extract_task_id_from_message(message_content)
        if not task_id:
            return None

        # 查找任务
        task = self.task_repository.find_by_harness_task_id(task_id)
        if not task:
            task = self.task_repository.find_by_id(task_id)

        return task

    def get_pending_reply_tasks(self) -> List[Task]:
        """获取等待回复的任务

        Returns:
            List[Task]: 等待回复的任务列表
        """
        return self.task_repository.find_by_status(TaskStatus.SENT)
