"""
API网关模块
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import json

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository


class TaskNotFoundError(Exception):
    """任务不存在异常"""
    pass


class InvalidReplyError(Exception):
    """无效回复异常"""
    pass


class InvalidCallbackError(Exception):
    """无效回调异常"""
    pass


class MessageNotFoundError(Exception):
    """消息不存在异常"""
    pass


class DuplicateReplyError(Exception):
    """重复回复异常"""
    pass


class TaskTimeoutError(Exception):
    """任务超时异常"""
    pass


class MaxRetriesExceededError(Exception):
    """超过最大重试次数异常"""
    pass


class InvalidRetryError(Exception):
    """无效重试异常"""
    pass


class InvalidImportError(Exception):
    """无效导入异常"""
    pass


class APIGateway:
    """API网关类"""

    def __init__(self, session=None, config=None):
        """初始化API网关"""
        self.task_repository = TaskRepository(session)
        self.config = config

    def get_pending_tasks(self) -> List[Task]:
        """获取待确认任务"""
        return self.task_repository.find_by_status(TaskStatus.PENDING)

    def submit_user_reply(self, task_id: str, reply_text: str, user_id: str) -> bool:
        """提交用户回复"""
        # 查找任务
        task = self.task_repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f'Task {task_id} not found')

        # 验证任务状态
        if task.status not in [TaskStatus.SENT, TaskStatus.REPLIED]:
            raise InvalidReplyError(f'Task {task_id} is not in a valid state for reply')

        # 验证回复内容
        if not reply_text or not reply_text.strip():
            raise InvalidReplyError('Reply text cannot be empty')

        # 更新任务状态
        task.status = TaskStatus.REPLIED
        task.user_reply = reply_text
        task.user_id = user_id

        self.task_repository.save(task)
        return True

    def handle_feishu_callback(self, callback_data: dict) -> bool:
        """处理飞书回调"""
        # 验证回调数据
        if 'event' not in callback_data:
            raise InvalidCallbackError('Missing event data')

        event = callback_data['event']
        if 'message' not in event:
            raise InvalidCallbackError('Missing message data')

        message = event['message']
        required_fields = ['content', 'message_type', 'open_id', 'message_id']
        for field in required_fields:
            if field not in message:
                raise InvalidCallbackError(f'Missing required field: {field}')

        # 查找任务
        task = self.task_repository.find_by_id(message['message_id'])
        if not task:
            raise MessageNotFoundError(f'Message {message["message_id"]} not found')

        # 检查任务状态
        if task.status == TaskStatus.REPLIED:
            raise DuplicateReplyError(f'Task {task.id} already replied')

        if task.status == TaskStatus.TIMEOUT:
            raise TaskTimeoutError(f'Task {task.id} has timed out')

        # 更新任务状态
        task.status = TaskStatus.REPLIED
        task.user_reply = message['content']
        task.user_id = message['open_id']

        self.task_repository.save(task)
        return True

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.task_repository.find_by_id(task_id)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务"""
        return self.task_repository.find_by_status(status)

    def get_timeout_tasks(self) -> List[Task]:
        """获取超时任务"""
        return self.task_repository.find_timeout_tasks()

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        task = self.task_repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f'Task {task_id} not found')

        return self.task_repository.update_status(task_id, status)

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        task = self.task_repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f'Task {task_id} not found')

        return self.task_repository.delete(task_id)

    def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息"""
        return {
            'total': self.task_repository.count_by_status(TaskStatus.PENDING) +
                    self.task_repository.count_by_status(TaskStatus.SENT) +
                    self.task_repository.count_by_status(TaskStatus.REPLIED) +
                    self.task_repository.count_by_status(TaskStatus.COMPLETED) +
                    self.task_repository.count_by_status(TaskStatus.TIMEOUT) +
                    self.task_repository.count_by_status(TaskStatus.FAILED),
            'pending': self.task_repository.count_by_status(TaskStatus.PENDING),
            'sent': self.task_repository.count_by_status(TaskStatus.SENT),
            'replied': self.task_repository.count_by_status(TaskStatus.REPLIED),
            'completed': self.task_repository.count_by_status(TaskStatus.COMPLETED),
            'timeout': self.task_repository.count_by_status(TaskStatus.TIMEOUT),
            'failed': self.task_repository.count_by_status(TaskStatus.FAILED)
        }

    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task = self.task_repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f'Task {task_id} not found')

        # 检查任务状态
        if task.status not in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
            raise InvalidRetryError(f'Task {task_id} cannot be retried')

        # 检查重试次数
        max_retry_count = 3  # 默认值
        if self.config:
            max_retry_count = self.config.max_retry_count

        if task.retry_count >= max_retry_count:
            raise MaxRetriesExceededError(f'Task {task_id} has exceeded max retries')

        # 重置任务状态
        task.status = TaskStatus.PENDING
        task.retry_count += 1

        self.task_repository.save(task)
        return True

    def search_tasks_by_content(self, query: str) -> List[Task]:
        """按内容搜索任务"""
        if not query:
            return self.task_repository.find_all()

        all_tasks = self.task_repository.find_all()
        return [task for task in all_tasks if query.lower() in task.content.lower()]

    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self.task_repository.find_all()

    def export_tasks_to_json(self) -> str:
        """导出任务为JSON"""
        tasks = self.task_repository.find_all()
        tasks_data = [task.to_dict() for task in tasks]
        return json.dumps(tasks_data, ensure_ascii=False)

    def import_tasks_from_json(self, json_data: str) -> int:
        """从JSON导入任务"""
        try:
            tasks_data = json.loads(json_data)
        except json.JSONDecodeError:
            raise InvalidImportError('Invalid JSON format')

        if not isinstance(tasks_data, list):
            raise InvalidImportError('JSON data must be a list')

        imported_count = 0
        for task_data in tasks_data:
            # 验证必要字段
            required_fields = ['id', 'harness_task_id', 'content']
            for field in required_fields:
                if field not in task_data:
                    raise InvalidImportError(f'Missing required field: {field}')

            # 创建任务对象
            task = Task(
                id=task_data['id'],
                harness_task_id=task_data['harness_task_id'],
                content=task_data['content'],
                context=task_data.get('context', {}),
                status=TaskStatus(task_data.get('status', 'pending'))
            )

            self.task_repository.save(task)
            imported_count += 1

        return imported_count

    def cleanup_old_tasks(self, days: int, status: TaskStatus = None) -> int:
        """清理旧任务"""
        # 使用 naive datetime 以兼容 SQLite（SQLite 不存储时区信息）
        cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

        if status:
            tasks = self.task_repository.find_by_status(status)
        else:
            tasks = self.task_repository.find_all()

        deleted_count = 0
        for task in tasks:
            if task.created_at < cutoff_date:
                self.task_repository.delete(task.id)
                deleted_count += 1

        return deleted_count