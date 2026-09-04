"""
轮询调度器模块
"""
import logging
import threading
from typing import List

from src.models.task import Task
from src.services.task_discovery import TaskDiscovery
from src.services.harness_client import HarnessConnectionError, HarnessAPIError

logger = logging.getLogger(__name__)


class PollingScheduler:
    """轮询调度器"""

    def __init__(self, task_discovery: TaskDiscovery, interval_seconds: int = 5):
        """初始化轮询调度器

        Args:
            task_discovery: 任务发现模块
            interval_seconds: 轮询间隔（秒）
        """
        self.task_discovery = task_discovery
        self.interval_seconds = interval_seconds
        self._is_running = threading.Event()
        self._thread = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._is_running.is_set()

    def start(self):
        """启动轮询"""
        if self._is_running.is_set():
            logger.warning('Polling scheduler is already running')
            return

        logger.info(f'Starting polling scheduler with interval {self.interval_seconds}s')
        self._is_running.set()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止轮询"""
        if not self._is_running.is_set():
            logger.warning('Polling scheduler is not running')
            return

        logger.info('Stopping polling scheduler')
        self._is_running.clear()
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval_seconds + 1)
            self._thread = None

    def poll_once(self) -> List[Task]:
        """执行一次轮询

        Returns:
            List[Task]: 新发现的任务列表
        """
        try:
            tasks = self.task_discovery.discover_pending_tasks()
            if tasks:
                logger.info(f'Poll discovered {len(tasks)} new tasks')
            return tasks
        except HarnessConnectionError as e:
            logger.error(f'Poll failed - connection error: {e}')
            return []
        except HarnessAPIError as e:
            logger.error(f'Poll failed - API error: {e}')
            return []
        except Exception as e:
            logger.error(f'Poll failed - unexpected error: {e}', exc_info=True)
            return []

    def _poll_loop(self):
        """轮询循环"""
        logger.info('Polling loop started')
        while not self._stop_event.is_set():
            self.poll_once()
            self._stop_event.wait(self.interval_seconds)
        logger.info('Polling loop stopped')
