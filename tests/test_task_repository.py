"""
任务仓库模块测试
基于接口签名契约设计测试用例
"""
import pytest
from datetime import datetime, timedelta, timezone
from src.models.task import Task, TaskStatus


class TestTaskRepository:
    """任务仓库测试"""

    def test_save_task(self, db_session, sample_task):
        """测试保存任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        saved_task = repo.save(sample_task)

        assert saved_task.id == 'task_123'
        assert saved_task.harness_task_id == 'harness_456'
        assert saved_task.content == '请确认以下操作：删除用户数据'

        # 验证数据库中存在
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task is not None

    def test_save_multiple_tasks(self, db_session, sample_tasks):
        """测试保存多个任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        for task in sample_tasks:
            repo.save(task)

        # 验证所有任务都保存成功
        tasks = db_session.query(Task).all()
        assert len(tasks) == 3

    def test_find_by_id_existing(self, db_session, sample_task):
        """测试根据ID查找存在的任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        repo.save(sample_task)

        found_task = repo.find_by_id('task_123')

        assert found_task is not None
        assert found_task.id == 'task_123'
        assert found_task.harness_task_id == 'harness_456'

    def test_find_by_id_non_existing(self, db_session):
        """测试根据ID查找不存在的任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        found_task = repo.find_by_id('non_existing_task')

        assert found_task is None

    def test_find_by_status(self, db_session, sample_tasks):
        """测试根据状态查找任务"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            repo.save(task)

        # 按状态查询
        pending_tasks = repo.find_by_status(TaskStatus.PENDING)
        sent_tasks = repo.find_by_status(TaskStatus.SENT)
        completed_tasks = repo.find_by_status(TaskStatus.COMPLETED)

        assert len(pending_tasks) == 1
        assert len(sent_tasks) == 1
        assert len(completed_tasks) == 1
        assert pending_tasks[0].id == 'task_0'
        assert sent_tasks[0].id == 'task_1'
        assert completed_tasks[0].id == 'task_2'

    def test_find_by_status_empty(self, db_session):
        """测试根据状态查找任务（空结果）"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)
        tasks = repo.find_by_status(TaskStatus.PENDING)

        assert len(tasks) == 0

    def test_update_status_success(self, db_session, sample_task):
        """测试更新任务状态成功"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)
        repo.save(sample_task)

        # 更新状态
        result = repo.update_status('task_123', TaskStatus.SENT)

        assert result is True

        # 验证更新
        updated_task = repo.find_by_id('task_123')
        assert updated_task.status == TaskStatus.SENT

    def test_update_status_non_existing(self, db_session):
        """测试更新不存在任务的状态"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)

        # 更新不存在的任务
        result = repo.update_status('non_existing_task', TaskStatus.SENT)

        assert result is False

    def test_update_status_with_additional_fields(self, db_session, sample_task):
        """测试更新任务状态和额外字段"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)
        repo.save(sample_task)

        # 更新状态和额外字段
        result = repo.update_status(
            'task_123',
            TaskStatus.REPLIED,
            user_reply='确认执行',
            user_id='user_456',
            feishu_message_id='msg_789'
        )

        assert result is True

        # 验证更新
        updated_task = repo.find_by_id('task_123')
        assert updated_task.status == TaskStatus.REPLIED
        assert updated_task.user_reply == '确认执行'
        assert updated_task.user_id == 'user_456'
        assert updated_task.feishu_message_id == 'msg_789'

    def test_find_timeout_tasks(self, db_session, sample_tasks):
        """测试查找超时任务"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)

        # 设置超时时间
        sample_tasks[0].timeout_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        sample_tasks[0].status = TaskStatus.SENT

        sample_tasks[1].timeout_at = datetime.now(timezone.utc) + timedelta(seconds=300)
        sample_tasks[1].status = TaskStatus.SENT

        sample_tasks[2].timeout_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            repo.save(task)

        # 查找超时任务
        timeout_tasks = repo.find_timeout_tasks()

        assert len(timeout_tasks) == 1
        assert timeout_tasks[0].id == 'task_0'

    def test_find_timeout_tasks_empty(self, db_session):
        """测试查找超时任务（空结果）"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        timeout_tasks = repo.find_timeout_tasks()

        assert len(timeout_tasks) == 0

    def test_find_timeout_tasks_with_limit(self, db_session, sample_tasks):
        """测试查找超时任务（带限制）"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)

        # 设置所有任务为超时
        for task in sample_tasks:
            task.timeout_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            task.status = TaskStatus.SENT
            repo.save(task)

        # 查找超时任务（限制2个）
        timeout_tasks = repo.find_timeout_tasks(limit=2)

        assert len(timeout_tasks) == 2

    def test_delete_task(self, db_session, sample_task):
        """测试删除任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        repo.save(sample_task)

        # 删除任务
        result = repo.delete('task_123')

        assert result is True

        # 验证删除
        deleted_task = repo.find_by_id('task_123')
        assert deleted_task is None

    def test_delete_non_existing_task(self, db_session):
        """测试删除不存在的任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        # 删除不存在的任务
        result = repo.delete('non_existing_task')

        assert result is False

    def test_count_by_status(self, db_session, sample_tasks):
        """测试按状态统计任务数量"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.PENDING

        for task in sample_tasks:
            repo.save(task)

        # 统计数量
        pending_count = repo.count_by_status(TaskStatus.PENDING)
        sent_count = repo.count_by_status(TaskStatus.SENT)
        completed_count = repo.count_by_status(TaskStatus.COMPLETED)

        assert pending_count == 2
        assert sent_count == 1
        assert completed_count == 0

    def test_find_all(self, db_session, sample_tasks):
        """测试查找所有任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        for task in sample_tasks:
            repo.save(task)

        # 查找所有任务
        all_tasks = repo.find_all()

        assert len(all_tasks) == 3

    def test_find_all_with_pagination(self, db_session, sample_tasks):
        """测试查找所有任务（带分页）"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        for task in sample_tasks:
            repo.save(task)

        # 分页查询
        page1 = repo.find_all(limit=2, offset=0)
        page2 = repo.find_all(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 1

    def test_find_all_with_ordering(self, db_session, sample_tasks):
        """测试查找所有任务（带排序）"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import Task

        repo = TaskRepository(db_session)

        # 设置不同的创建时间
        sample_tasks[0].created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        sample_tasks[1].created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        sample_tasks[2].created_at = datetime.now(timezone.utc)

        for task in sample_tasks:
            repo.save(task)

        # 按创建时间升序查询
        tasks_asc = repo.find_all(order_by=Task.created_at, order='asc')
        assert tasks_asc[0].id == 'task_0'
        assert tasks_asc[1].id == 'task_1'
        assert tasks_asc[2].id == 'task_2'

        # 按创建时间降序查询
        tasks_desc = repo.find_all(order_by=Task.created_at, order='desc')
        assert tasks_desc[0].id == 'task_2'
        assert tasks_desc[1].id == 'task_1'
        assert tasks_desc[2].id == 'task_0'

    def test_find_by_harness_task_id(self, db_session, sample_task):
        """测试根据Harness任务ID查找任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        repo.save(sample_task)

        found_task = repo.find_by_harness_task_id('harness_456')

        assert found_task is not None
        assert found_task.id == 'task_123'
        assert found_task.harness_task_id == 'harness_456'

    def test_find_by_harness_task_id_non_existing(self, db_session):
        """测试根据Harness任务ID查找不存在的任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        found_task = repo.find_by_harness_task_id('non_existing_harness_id')

        assert found_task is None

    def test_exists_by_id(self, db_session, sample_task):
        """测试检查任务是否存在"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        repo.save(sample_task)

        assert repo.exists_by_id('task_123') is True
        assert repo.exists_by_id('non_existing_task') is False

    def test_bulk_save(self, db_session, sample_tasks):
        """测试批量保存任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)
        saved_tasks = repo.bulk_save(sample_tasks)

        assert len(saved_tasks) == 3

        # 验证所有任务都保存成功
        all_tasks = repo.find_all()
        assert len(all_tasks) == 3

    def test_bulk_update_status(self, db_session, sample_tasks):
        """测试批量更新任务状态"""
        from src.repositories.task_repository import TaskRepository
        from src.models.task import TaskStatus

        repo = TaskRepository(db_session)

        # 保存任务
        for task in sample_tasks:
            repo.save(task)

        # 批量更新状态
        task_ids = ['task_0', 'task_1', 'task_2']
        result = repo.bulk_update_status(task_ids, TaskStatus.SENT)

        assert result == 3  # 更新了3个任务

        # 验证更新
        for task_id in task_ids:
            task = repo.find_by_id(task_id)
            assert task.status == TaskStatus.SENT

    def test_bulk_delete(self, db_session, sample_tasks):
        """测试批量删除任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        # 保存任务
        for task in sample_tasks:
            repo.save(task)

        # 批量删除
        task_ids = ['task_0', 'task_1', 'task_2']
        result = repo.bulk_delete(task_ids)

        assert result == 3  # 删除了3个任务

        # 验证删除
        all_tasks = repo.find_all()
        assert len(all_tasks) == 0

    def test_find_tasks_created_between(self, db_session, sample_tasks):
        """测试查找指定时间范围内创建的任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        # 设置不同的创建时间
        sample_tasks[0].created_at = datetime.now(timezone.utc) - timedelta(hours=3)
        sample_tasks[1].created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        sample_tasks[2].created_at = datetime.now(timezone.utc) - timedelta(hours=1)

        for task in sample_tasks:
            repo.save(task)

        # 查找2小时前到1小时前创建的任务
        start_time = datetime.now(timezone.utc) - timedelta(hours=2, minutes=30)
        end_time = datetime.now(timezone.utc) - timedelta(hours=1, minutes=30)

        tasks = repo.find_tasks_created_between(start_time, end_time)

        assert len(tasks) == 1
        assert tasks[0].id == 'task_1'

    def test_find_tasks_with_retry_count_less_than(self, db_session, sample_tasks):
        """测试查找重试次数小于指定值的任务"""
        from src.repositories.task_repository import TaskRepository

        repo = TaskRepository(db_session)

        # 设置不同的重试次数
        sample_tasks[0].retry_count = 0
        sample_tasks[1].retry_count = 1
        sample_tasks[2].retry_count = 3

        for task in sample_tasks:
            repo.save(task)

        # 查找重试次数小于2的任务
        tasks = repo.find_tasks_with_retry_count_less_than(2)

        assert len(tasks) == 2
        assert tasks[0].id == 'task_0'
        assert tasks[1].id == 'task_1'