"""
数据库模型模块测试
基于接口签名契约设计测试用例
"""
import pytest
from datetime import datetime, timedelta, timezone
from src.models.task import Task, TaskStatus


class TestTaskModel:
    """任务模型测试"""

    def test_task_creation(self, db_session, sample_task):
        """测试任务创建"""
        db_session.add(sample_task)
        db_session.commit()

        # 查询任务
        task = db_session.query(Task).filter_by(id='task_123').first()

        assert task is not None
        assert task.id == 'task_123'
        assert task.harness_task_id == 'harness_456'
        assert task.content == '请确认以下操作：删除用户数据'
        assert task.context == {'user_id': 'user_789', 'action': 'delete_user_data'}
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0
        assert task.feishu_message_id is None
        assert task.user_reply is None
        assert task.user_id is None

    def test_task_default_values(self, db_session):
        """测试任务默认值"""
        from src.models.task import Task, TaskStatus

        task = Task(
            id='task_default',
            harness_task_id='harness_default',
            content='测试默认值',
            context={},
            status=TaskStatus.PENDING
        )

        db_session.add(task)
        db_session.commit()

        # 验证默认值
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.retry_count == 0
        assert task.feishu_message_id is None
        assert task.user_reply is None
        assert task.user_id is None
        assert task.timeout_at is None

    def test_task_status_enum(self):
        """测试任务状态枚举"""
        from src.models.task import TaskStatus

        assert TaskStatus.PENDING.value == 'pending'
        assert TaskStatus.SENT.value == 'sent'
        assert TaskStatus.REPLIED.value == 'replied'
        assert TaskStatus.COMPLETED.value == 'completed'
        assert TaskStatus.TIMEOUT.value == 'timeout'
        assert TaskStatus.FAILED.value == 'failed'

    def test_task_status_transitions(self, db_session, sample_task):
        """测试任务状态转换"""
        db_session.add(sample_task)
        db_session.commit()

        # 待确认 -> 已发送飞书
        sample_task.status = TaskStatus.SENT
        sample_task.feishu_message_id = 'msg_789'
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.SENT
        assert task.feishu_message_id == 'msg_789'

        # 已发送飞书 -> 已回复
        sample_task.status = TaskStatus.REPLIED
        sample_task.user_reply = '确认执行'
        sample_task.user_id = 'user_456'
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.REPLIED
        assert task.user_reply == '确认执行'
        assert task.user_id == 'user_456'

        # 已回复 -> 已完成
        sample_task.status = TaskStatus.COMPLETED
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.COMPLETED

    def test_task_timeout_status(self, db_session, sample_task):
        """测试任务超时状态"""
        db_session.add(sample_task)
        db_session.commit()

        # 设置超时时间（使用 naive datetime 以匹配 SQLite 存储格式）
        sample_task.timeout_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        sample_task.status = TaskStatus.TIMEOUT
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.TIMEOUT
        assert task.timeout_at < datetime.now(timezone.utc).replace(tzinfo=None)

    def test_task_failed_status(self, db_session, sample_task):
        """测试任务失败状态"""
        db_session.add(sample_task)
        db_session.commit()

        sample_task.status = TaskStatus.FAILED
        sample_task.retry_count = 3
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 3

    def test_task_retry_count_increment(self, db_session, sample_task):
        """测试任务重试次数递增"""
        db_session.add(sample_task)
        db_session.commit()

        # 增加重试次数
        sample_task.retry_count += 1
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.retry_count == 1

        # 再次增加
        sample_task.retry_count += 1
        db_session.commit()

        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.retry_count == 2

    def test_task_context_json_storage(self, db_session):
        """测试任务上下文JSON存储"""
        from src.models.task import Task, TaskStatus

        complex_context = {
            'user_id': 'user_789',
            'action': 'delete_user_data',
            'metadata': {
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0',
                'timestamp': '2026-09-03T10:00:00Z'
            },
            'options': ['option1', 'option2', 'option3']
        }

        task = Task(
            id='task_json',
            harness_task_id='harness_json',
            content='测试JSON存储',
            context=complex_context,
            status=TaskStatus.PENDING
        )

        db_session.add(task)
        db_session.commit()

        # 查询验证
        queried_task = db_session.query(Task).filter_by(id='task_json').first()
        assert queried_task.context == complex_context
        assert queried_task.context['metadata']['ip_address'] == '192.168.1.100'
        assert len(queried_task.context['options']) == 3

    def test_task_timestamps_auto_update(self, db_session, sample_task):
        """测试任务时间戳自动更新"""
        db_session.add(sample_task)
        db_session.commit()

        original_created_at = sample_task.created_at
        original_updated_at = sample_task.updated_at

        # 修改任务内容
        sample_task.content = '更新后的内容'
        db_session.commit()

        # 验证时间戳
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.created_at == original_created_at  # 创建时间不变
        assert task.updated_at > original_updated_at  # 更新时间变化

    def test_task_find_by_status(self, db_session, sample_tasks):
        """测试按状态查找任务"""
        from src.models.task import Task, TaskStatus

        # 添加多个任务
        for task in sample_tasks:
            db_session.add(task)

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.COMPLETED

        db_session.commit()

        # 按状态查询
        pending_tasks = db_session.query(Task).filter_by(status=TaskStatus.PENDING).all()
        sent_tasks = db_session.query(Task).filter_by(status=TaskStatus.SENT).all()
        completed_tasks = db_session.query(Task).filter_by(status=TaskStatus.COMPLETED).all()

        assert len(pending_tasks) == 1
        assert len(sent_tasks) == 1
        assert len(completed_tasks) == 1
        assert pending_tasks[0].id == 'task_0'
        assert sent_tasks[0].id == 'task_1'
        assert completed_tasks[0].id == 'task_2'

    def test_task_find_timeout_tasks(self, db_session, sample_tasks):
        """测试查找超时任务"""
        from src.models.task import Task, TaskStatus

        # 设置超时时间（使用 naive datetime 以匹配 SQLite 存储格式）
        sample_tasks[0].timeout_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        sample_tasks[0].status = TaskStatus.SENT

        sample_tasks[1].timeout_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=300)
        sample_tasks[1].status = TaskStatus.SENT

        sample_tasks[2].timeout_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)

        db_session.commit()

        # 查找超时任务（已发送且已超时，使用 naive datetime）
        timeout_tasks = db_session.query(Task).filter(
            Task.status == TaskStatus.SENT,
            Task.timeout_at < datetime.now(timezone.utc).replace(tzinfo=None)
        ).all()

        assert len(timeout_tasks) == 1
        assert timeout_tasks[0].id == 'task_0'

    def test_task_find_by_harness_task_id(self, db_session, sample_task):
        """测试按Harness任务ID查找任务"""
        db_session.add(sample_task)
        db_session.commit()

        task = db_session.query(Task).filter_by(harness_task_id='harness_456').first()

        assert task is not None
        assert task.id == 'task_123'
        assert task.harness_task_id == 'harness_456'

    def test_task_delete(self, db_session, sample_task):
        """测试删除任务"""
        db_session.add(sample_task)
        db_session.commit()

        # 删除任务
        db_session.delete(sample_task)
        db_session.commit()

        # 验证删除
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task is None

    def test_task_update_multiple_fields(self, db_session, sample_task):
        """测试更新多个字段"""
        db_session.add(sample_task)
        db_session.commit()

        # 更新多个字段
        sample_task.status = TaskStatus.REPLIED
        sample_task.user_reply = '确认执行'
        sample_task.user_id = 'user_456'
        sample_task.feishu_message_id = 'msg_789'
        sample_task.retry_count = 2
        db_session.commit()

        # 验证更新
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.REPLIED
        assert task.user_reply == '确认执行'
        assert task.user_id == 'user_456'
        assert task.feishu_message_id == 'msg_789'
        assert task.retry_count == 2

    def test_task_query_ordering(self, db_session, sample_tasks):
        """测试任务查询排序"""
        from src.models.task import Task

        # 设置不同的创建时间
        sample_tasks[0].created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        sample_tasks[1].created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        sample_tasks[2].created_at = datetime.now(timezone.utc)

        for task in sample_tasks:
            db_session.add(task)

        db_session.commit()

        # 按创建时间升序查询
        tasks_asc = db_session.query(Task).order_by(Task.created_at.asc()).all()
        assert tasks_asc[0].id == 'task_0'
        assert tasks_asc[1].id == 'task_1'
        assert tasks_asc[2].id == 'task_2'

        # 按创建时间降序查询
        tasks_desc = db_session.query(Task).order_by(Task.created_at.desc()).all()
        assert tasks_desc[0].id == 'task_2'
        assert tasks_desc[1].id == 'task_1'
        assert tasks_desc[2].id == 'task_0'

    def test_task_query_pagination(self, db_session, sample_tasks):
        """测试任务查询分页"""
        from src.models.task import Task

        # 添加多个任务
        for task in sample_tasks:
            db_session.add(task)

        db_session.commit()

        # 分页查询
        page1 = db_session.query(Task).limit(2).offset(0).all()
        page2 = db_session.query(Task).limit(2).offset(2).all()

        assert len(page1) == 2
        assert len(page2) == 1

    def test_task_unique_constraint(self, db_session, sample_task):
        """测试任务唯一约束"""
        db_session.add(sample_task)
        db_session.commit()

        # 尝试添加相同ID的任务
        duplicate_task = Task(
            id='task_123',  # 相同ID
            harness_task_id='harness_789',
            content='重复任务',
            context={},
            status=TaskStatus.PENDING
        )

        db_session.add(duplicate_task)

        with pytest.raises(Exception):  # 应该抛出唯一约束异常
            db_session.commit()

    def test_task_nullable_fields(self, db_session):
        """测试任务可空字段"""
        from src.models.task import Task, TaskStatus

        task = Task(
            id='task_nullable',
            harness_task_id='harness_nullable',
            content='测试可空字段',
            context=None,  # 可空
            status=TaskStatus.PENDING,
            feishu_message_id=None,  # 可空
            user_reply=None,  # 可空
            user_id=None,  # 可空
            timeout_at=None  # 可空
        )

        db_session.add(task)
        db_session.commit()

        # 验证可空字段
        queried_task = db_session.query(Task).filter_by(id='task_nullable').first()
        assert queried_task.context is None
        assert queried_task.feishu_message_id is None
        assert queried_task.user_reply is None
        assert queried_task.user_id is None
        assert queried_task.timeout_at is None

    def test_task_large_content(self, db_session):
        """测试任务大内容"""
        from src.models.task import Task, TaskStatus

        large_content = 'A' * 10000  # 10KB内容

        task = Task(
            id='task_large',
            harness_task_id='harness_large',
            content=large_content,
            context={},
            status=TaskStatus.PENDING
        )

        db_session.add(task)
        db_session.commit()

        # 验证大内容
        queried_task = db_session.query(Task).filter_by(id='task_large').first()
        assert len(queried_task.content) == 10000
        assert queried_task.content == large_content