"""回复提交服务模块

负责将用户回复提交到 DeepSeek Harness。
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository
from src.services.harness_client import HarnessClient, HarnessConnectionError, HarnessAPIError

logger = logging.getLogger(__name__)


@dataclass
class ReplySubmitResult:
    """回复提交结果"""

    task_id: str
    success: bool
    message: str
    harness_response: Optional[dict] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'success': self.success,
            'message': self.message,
            'harness_response': self.harness_response,
        }


class ReplySubmitter:
    """回复提交服务"""

    def __init__(self, harness_client: HarnessClient, task_repository: TaskRepository):
        """初始化回复提交服务

        Args:
            harness_client: DeepSeek Harness 客户端
            task_repository: 任务仓库
        """
        self.harness_client = harness_client
        self.task_repository = task_repository

    def submit_reply(self, task_id: str, reply_text: str, user_id: str) -> ReplySubmitResult:
        """提交回复到 DeepSeek Harness

        Args:
            task_id: 任务ID
            reply_text: 回复文本
            user_id: 用户ID

        Returns:
            ReplySubmitResult: 提交结果
        """
        # 查找任务
        task = self.task_repository.find_by_id(task_id)
        if not task:
            task = self.task_repository.find_by_harness_task_id(task_id)

        if not task:
            return ReplySubmitResult(
                task_id=task_id,
                success=False,
                message=f"Task not found: {task_id}",
            )

        # 检查任务状态
        if task.status != TaskStatus.REPLIED:
            return ReplySubmitResult(
                task_id=task_id,
                success=False,
                message=f"Task status is {task.status.value}, expected REPLIED",
            )

        # 提交到 Harness
        try:
            harness_success = self.harness_client.submit_reply(
                task_id=task.harness_task_id,
                reply_text=reply_text,
                user_id=user_id,
            )

            if harness_success:
                # 更新任务状态为已完成
                task.status = TaskStatus.COMPLETED
                self.task_repository.save(task)

                logger.info("Reply submitted successfully for task %s", task_id)
                return ReplySubmitResult(
                    task_id=task_id,
                    success=True,
                    message="Reply submitted successfully",
                )
            else:
                return ReplySubmitResult(
                    task_id=task_id,
                    success=False,
                    message="Harness API returned failure",
                )

        except HarnessConnectionError as e:
            logger.error("Connection error submitting reply for task %s: %s", task_id, e)
            return ReplySubmitResult(
                task_id=task_id,
                success=False,
                message=f"Connection error: {str(e)}",
            )
        except HarnessAPIError as e:
            logger.error("API error submitting reply for task %s: %s", task_id, e)
            return ReplySubmitResult(
                task_id=task_id,
                success=False,
                message=f"API error: {str(e)}",
            )
        except Exception as e:
            logger.error("Unexpected error submitting reply for task %s: %s", task_id, e)
            return ReplySubmitResult(
                task_id=task_id,
                success=False,
                message=f"Unexpected error: {str(e)}",
            )

    def submit_pending_replies(self) -> List[ReplySubmitResult]:
        """提交所有待处理的回复

        Returns:
            List[ReplySubmitResult]: 提交结果列表
        """
        # 获取所有已回复的任务
        replied_tasks = self.task_repository.find_by_status(TaskStatus.REPLIED)
        results = []

        for task in replied_tasks:
            if task.user_reply and task.user_id:
                result = self.submit_reply(
                    task_id=task.id,
                    reply_text=task.user_reply,
                    user_id=task.user_id,
                )
                results.append(result)

        logger.info("Submitted %d pending replies", len(results))
        return results

    def retry_failed_submissions(self, max_retries: int = 3) -> List[ReplySubmitResult]:
        """重试失败的提交

        Args:
            max_retries: 最大重试次数

        Returns:
            List[ReplySubmitResult]: 重试结果列表
        """
        # 获取所有已回复但未完成的任务
        replied_tasks = self.task_repository.find_by_status(TaskStatus.REPLIED)
        results = []

        for task in replied_tasks:
            if task.user_reply and task.user_id:
                # 检查重试次数
                if task.retry_count >= max_retries:
                    logger.warning("Task %s exceeded max retries (%d), skipping", task.id, max_retries)
                    continue

                # 增加重试计数
                task.retry_count += 1
                self.task_repository.save(task)

                result = self.submit_reply(
                    task_id=task.id,
                    reply_text=task.user_reply,
                    user_id=task.user_id,
                )
                results.append(result)

        logger.info("Retried %d failed submissions", len(results))
        return results

    def get_submission_stats(self) -> dict:
        """获取提交统计信息

        Returns:
            dict: 统计信息
        """
        replied_count = self.task_repository.count_by_status(TaskStatus.REPLIED)
        completed_count = self.task_repository.count_by_status(TaskStatus.COMPLETED)
        failed_count = self.task_repository.count_by_status(TaskStatus.FAILED)

        return {
            'replied': replied_count,
            'completed': completed_count,
            'failed': failed_count,
            'pending_submission': replied_count,
        }
