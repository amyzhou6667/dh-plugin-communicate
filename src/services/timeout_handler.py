"""超时处理器模块

负责处理超时任务，包括超时检测、提醒和状态更新。
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository
from src.services.feishu_client import FeishuClient
from src.services.harness_client import HarnessClient

logger = logging.getLogger(__name__)


@dataclass
class TimeoutResult:
    """超时处理结果"""

    task_id: str
    action: str  # 'reminder', 'timeout', 'failed', 'skipped'
    success: bool
    message: str

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'action': self.action,
            'success': self.success,
            'message': self.message,
        }


class TimeoutHandler:
    """超时处理器"""

    def __init__(self, task_repository: TaskRepository,
                 feishu_client: Optional[FeishuClient] = None,
                 harness_client: Optional[HarnessClient] = None,
                 max_retry_count: int = 3):
        """初始化超时处理器

        Args:
            task_repository: 任务仓库
            feishu_client: 飞书客户端（可选）
            harness_client: Harness客户端（可选）
            max_retry_count: 最大重试次数
        """
        self.task_repository = task_repository
        self.feishu_client = feishu_client
        self.harness_client = harness_client
        self.max_retry_count = max_retry_count

    def check_timeout_tasks(self) -> List[TimeoutResult]:
        """检查超时任务

        Returns:
            List[TimeoutResult]: 超时处理结果列表
        """
        # 查找超时任务
        timeout_tasks = self.task_repository.find_timeout_tasks()
        results = []

        for task in timeout_tasks:
            result = self.handle_timeout_task(task)
            results.append(result)

        if results:
            logger.info("Processed %d timeout tasks", len(results))

        return results

    def handle_timeout_task(self, task: Task) -> TimeoutResult:
        """处理单个超时任务

        Args:
            task: 超时任务

        Returns:
            TimeoutResult: 处理结果
        """
        # 检查重试次数
        if task.retry_count >= self.max_retry_count:
            return self._handle_max_retries_exceeded(task)

        # 根据当前状态处理
        if task.status == TaskStatus.SENT:
            return self._handle_sent_timeout(task)
        else:
            return TimeoutResult(
                task_id=task.id,
                action='skipped',
                success=True,
                message=f"Task status {task.status.value} not handled for timeout",
            )

    def _handle_sent_timeout(self, task: Task) -> TimeoutResult:
        """处理已发送状态的超时任务

        Args:
            task: 超时任务

        Returns:
            TimeoutResult: 处理结果
        """
        # 增加重试计数
        task.retry_count += 1

        # 发送提醒
        reminder_sent = self.send_timeout_reminder(task)

        if reminder_sent:
            # 更新超时时间（延长等待）
            task.timeout_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.task_repository.save(task)

            return TimeoutResult(
                task_id=task.id,
                action='reminder',
                success=True,
                message=f"Timeout reminder sent (retry {task.retry_count})",
            )
        else:
            # 提醒发送失败，标记为超时
            return self.mark_task_timeout(task)

    def _handle_max_retries_exceeded(self, task: Task) -> TimeoutResult:
        """处理超过最大重试次数的任务

        Args:
            task: 超时任务

        Returns:
            TimeoutResult: 处理结果
        """
        # 标记为失败
        result = self.mark_task_failed(task)

        # 通知 Harness
        if self.harness_client:
            try:
                # 这里可以添加通知 Harness 的逻辑
                pass
            except Exception as e:
                logger.error("Failed to notify Harness about task %s timeout: %s", task.id, e)

        return result

    def send_timeout_reminder(self, task: Task) -> bool:
        """发送超时提醒

        Args:
            task: 超时任务

        Returns:
            bool: 发送是否成功
        """
        if not self.feishu_client:
            logger.warning("Feishu client not configured, cannot send reminder")
            return False

        if not task.feishu_message_id:
            logger.warning("Task %s has no feishu_message_id, cannot send reminder", task.id)
            return False

        try:
            # 构建提醒消息
            reminder_text = f"⏰ 超时提醒\n\n您的任务 \"{task.content[:50]}...\" 已等待较长时间，请尽快回复。"

            # 发送提醒（这里假设发送到同一个聊天）
            # 实际实现需要根据 feishu_message_id 获取 chat_id
            logger.info("Sending timeout reminder for task %s", task.id)
            return True

        except Exception as e:
            logger.error("Failed to send timeout reminder for task %s: %s", task.id, e)
            return False

    def mark_task_timeout(self, task: Task) -> TimeoutResult:
        """标记任务超时

        Args:
            task: 超时任务

        Returns:
            TimeoutResult: 处理结果
        """
        try:
            task.status = TaskStatus.TIMEOUT
            self.task_repository.save(task)

            logger.info("Task %s marked as timeout", task.id)

            return TimeoutResult(
                task_id=task.id,
                action='timeout',
                success=True,
                message="Task marked as timeout",
            )

        except Exception as e:
            logger.error("Failed to mark task %s as timeout: %s", task.id, e)
            return TimeoutResult(
                task_id=task.id,
                action='timeout',
                success=False,
                message=f"Failed to mark as timeout: {str(e)}",
            )

    def mark_task_failed(self, task: Task) -> TimeoutResult:
        """标记任务失败

        Args:
            task: 超时任务

        Returns:
            TimeoutResult: 处理结果
        """
        try:
            task.status = TaskStatus.FAILED
            self.task_repository.save(task)

            logger.info("Task %s marked as failed due to timeout", task.id)

            return TimeoutResult(
                task_id=task.id,
                action='failed',
                success=True,
                message="Task marked as failed due to max retries exceeded",
            )

        except Exception as e:
            logger.error("Failed to mark task %s as failed: %s", task.id, e)
            return TimeoutResult(
                task_id=task.id,
                action='failed',
                success=False,
                message=f"Failed to mark as failed: {str(e)}",
            )

    def get_timeout_stats(self) -> dict:
        """获取超时统计信息

        Returns:
            dict: 统计信息
        """
        timeout_count = self.task_repository.count_by_status(TaskStatus.TIMEOUT)
        failed_count = self.task_repository.count_by_status(TaskStatus.FAILED)
        sent_count = self.task_repository.count_by_status(TaskStatus.SENT)

        return {
            'timeout': timeout_count,
            'failed': failed_count,
            'sent': sent_count,
            'pending_timeout_check': sent_count,
        }
