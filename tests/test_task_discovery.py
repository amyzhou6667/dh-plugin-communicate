"""
任务发现模块测试
基于接口签名契约设计测试用例
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone


class TestTaskDiscovery:
    """TaskDiscovery 测试"""

    def test_initialization(self):
        """测试任务发现模块初始化"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository

        mock_client = Mock(spec=HarnessClient)
        mock_repo = Mock(spec=TaskRepository)

        discovery = TaskDiscovery(mock_client, mock_repo)
        assert discovery.harness_client == mock_client
        assert discovery.task_repository == mock_repo

    def test_discover_pending_tasks_success(self, db_session):
        """测试发现待确认任务成功"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository
        from src.models.task import Task, TaskStatus

        # Mock HarnessClient
        mock_client = Mock(spec=HarnessClient)
        mock_client.get_pending_tasks.return_value = [
            {
                'id': 'harness_task_1',
                'content': '请确认操作',
                'context': {'action': 'delete'}
            },
            {
                'id': 'harness_task_2',
                'content': '请确认部署',
                'context': {'env': 'production'}
            }
        ]

        # 创建真实的 TaskRepository
        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)
        tasks = discovery.discover_pending_tasks()

        assert len(tasks) == 2
        assert tasks[0].harness_task_id == 'harness_task_1'
        assert tasks[1].harness_task_id == 'harness_task_2'
        assert all(task.status == TaskStatus.PENDING for task in tasks)

        # 验证数据库中存在任务
        saved_tasks = db_session.query(Task).all()
        assert len(saved_tasks) == 2

    def test_discover_pending_tasks_no_new(self, db_session):
        """测试没有新任务"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository

        # Mock HarnessClient 返回空列表
        mock_client = Mock(spec=HarnessClient)
        mock_client.get_pending_tasks.return_value = []

        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)
        tasks = discovery.discover_pending_tasks()

        assert len(tasks) == 0

    def test_discover_pending_tasks_filter_processed(self, db_session):
        """测试过滤已处理任务"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository
        from src.models.task import Task, TaskStatus

        # 先创建一个已处理的任务
        existing_task = Task(
            id='existing_task',
            harness_task_id='harness_task_1',
            content='已处理的任务',
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            timeout_at=datetime.now(timezone.utc) + timedelta(seconds=300)
        )
        db_session.add(existing_task)
        db_session.commit()

        # Mock HarnessClient 返回包含已处理任务的列表
        mock_client = Mock(spec=HarnessClient)
        mock_client.get_pending_tasks.return_value = [
            {
                'id': 'harness_task_1',  # 已处理
                'content': '已处理的任务',
                'context': {}
            },
            {
                'id': 'harness_task_2',  # 新任务
                'content': '新任务',
                'context': {}
            }
        ]

        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)
        tasks = discovery.discover_pending_tasks()

        # 应该只返回新任务
        assert len(tasks) == 1
        assert tasks[0].harness_task_id == 'harness_task_2'

    def test_discover_pending_tasks_all_processed(self, db_session):
        """测试所有任务已处理"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository
        from src.models.task import Task, TaskStatus

        # 创建已处理的任务
        existing_task = Task(
            id='existing_task',
            harness_task_id='harness_task_1',
            content='已处理的任务',
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            timeout_at=datetime.now(timezone.utc) + timedelta(seconds=300)
        )
        db_session.add(existing_task)
        db_session.commit()

        # Mock HarnessClient 返回已处理的任务
        mock_client = Mock(spec=HarnessClient)
        mock_client.get_pending_tasks.return_value = [
            {
                'id': 'harness_task_1',
                'content': '已处理的任务',
                'context': {}
            }
        ]

        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)
        tasks = discovery.discover_pending_tasks()

        assert len(tasks) == 0

    def test_discover_pending_tasks_connection_error(self, db_session):
        """测试连接失败"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient, HarnessConnectionError
        from src.repositories.task_repository import TaskRepository

        # Mock HarnessClient 抛出连接错误
        mock_client = Mock(spec=HarnessClient)
        mock_client.get_pending_tasks.side_effect = HarnessConnectionError('Connection refused')

        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)

        with pytest.raises(HarnessConnectionError):
            discovery.discover_pending_tasks()

    def test_filter_processed_tasks(self, db_session):
        """测试过滤已处理任务"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository
        from src.models.task import Task, TaskStatus

        # 创建已处理的任务
        existing_task = Task(
            id='existing_task',
            harness_task_id='harness_task_1',
            content='已处理的任务',
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            timeout_at=datetime.now(timezone.utc) + timedelta(seconds=300)
        )
        db_session.add(existing_task)
        db_session.commit()

        mock_client = Mock(spec=HarnessClient)
        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)

        harness_tasks = [
            {'id': 'harness_task_1', 'content': '已处理的任务'},
            {'id': 'harness_task_2', 'content': '新任务'}
        ]

        filtered_tasks = discovery.filter_processed_tasks(harness_tasks)

        assert len(filtered_tasks) == 1
        assert filtered_tasks[0]['id'] == 'harness_task_2'

    def test_filter_processed_tasks_empty(self, db_session):
        """测试过滤已处理任务（空列表）"""
        from src.services.task_discovery import TaskDiscovery
        from src.services.harness_client import HarnessClient
        from src.repositories.task_repository import TaskRepository

        mock_client = Mock(spec=HarnessClient)
        repo = TaskRepository(db_session)

        discovery = TaskDiscovery(mock_client, repo)

        harness_tasks = []
        filtered_tasks = discovery.filter_processed_tasks(harness_tasks)

        assert len(filtered_tasks) == 0
