"""
任务发现模块
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from src.models.task import Task, TaskStatus
from src.repositories.task_repository import TaskRepository
from src.services.harness_client import HarnessClient, HarnessConnectionError, HarnessAPIError

logger = logging.getLogger(__name__)


class TaskDiscovery:
    """任务发现模块"""

    def __init__(self, harness_client: HarnessClient, task_repository: TaskRepository, timeout_seconds: int = 300):
        """初始化任务发现模块

        Args:
            harness_client: DeepSeek Harness 客户端
            task_repository: 任务仓库
            timeout_seconds: 任务超时时间（秒），默认300秒
        """
        self.harness_client = harness_client
        self.task_repository = task_repository
        self.timeout_seconds = timeout_seconds

    def discover_pending_tasks(self) -> List[Task]:
        """发现待确认任务

        从 DeepSeek Harness 获取待确认任务，过滤已处理任务，创建新任务记录

        Returns:
            List[Task]: 新发现的任务列表

        Raises:
            HarnessConnectionError: 连接失败
            HarnessAPIError: API调用失败
        """
        # 从 Harness 获取待确认任务
        harness_tasks = self.harness_client.get_pending_tasks()
        logger.info(f'Fetched {len(harness_tasks)} tasks from Harness')

        # 过滤已处理任务
        new_tasks = self.filter_processed_tasks(harness_tasks)
        logger.info(f'Found {len(new_tasks)} new tasks after filtering')

        # 创建任务记录
        created_tasks = []
        for task_data in new_tasks:
            task = Task(
                id=f"task_{task_data['id']}",
                harness_task_id=task_data['id'],
                content=task_data.get('content', ''),
                context=task_data.get('context', {}),
                status=TaskStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                timeout_at=datetime.now(timezone.utc) + timedelta(seconds=self.timeout_seconds)
            )
            self.task_repository.save(task)
            created_tasks.append(task)
            logger.debug(f'Created task {task.id} from harness task {task_data["id"]}')

        logger.info(f'Discovered {len(created_tasks)} new pending tasks')
        return created_tasks

    def filter_processed_tasks(self, harness_tasks: List[dict]) -> List[dict]:
        """过滤已处理任务

        Args:
            harness_tasks: 从 Harness 获取的任务列表

        Returns:
            List[dict]: 未处理的任务列表
        """
        if not harness_tasks:
            return []

        # 获取所有已存在的 harness_task_id
        existing_harness_ids = self.task_repository.get_existing_harness_task_ids()
        logger.debug(f'Found {len(existing_harness_ids)} existing harness task IDs')

        # 过滤掉已存在的任务
        filtered = [
            task for task in harness_tasks
            if task['id'] not in existing_harness_ids
        ]
        logger.debug(f'Filtered {len(harness_tasks)} -> {len(filtered)} tasks')
        return filtered
