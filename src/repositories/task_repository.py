"""
任务仓库模块
"""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import desc, asc
from src.app import db
from src.models.task import Task, TaskStatus


class TaskRepository:
    """任务仓库类"""

    def __init__(self, session=None):
        """初始化任务仓库"""
        self.session = session or db.session

    def save(self, task: Task) -> Task:
        """保存任务"""
        try:
            self.session.add(task)
            self.session.commit()
            return task
        except Exception:
            self.session.rollback()
            raise

    def find_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID查找任务"""
        return self.session.query(Task).filter_by(id=task_id).first()

    def find_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态查找任务"""
        return self.session.query(Task).filter_by(status=status).all()

    def find_by_harness_task_id(self, harness_task_id: str) -> Optional[Task]:
        """根据Harness任务ID查找任务"""
        return self.session.query(Task).filter_by(harness_task_id=harness_task_id).first()

    def update_status(self, task_id: str, status: TaskStatus, **kwargs) -> bool:
        """更新任务状态"""
        try:
            task = self.find_by_id(task_id)
            if not task:
                return False

            task.status = status
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def find_timeout_tasks(self, limit: int = None) -> List[Task]:
        """查找超时任务"""
        query = self.session.query(Task).filter(
            Task.status == TaskStatus.SENT,
            Task.timeout_at < datetime.now(timezone.utc)
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def delete(self, task_id: str) -> bool:
        """删除任务"""
        try:
            task = self.find_by_id(task_id)
            if not task:
                return False

            self.session.delete(task)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def count_by_status(self, status: TaskStatus) -> int:
        """按状态统计任务数量"""
        return self.session.query(Task).filter_by(status=status).count()

    def find_all(self, limit: int = None, offset: int = None, order_by=None, order: str = 'asc') -> List[Task]:
        """查找所有任务"""
        query = self.session.query(Task)

        if order_by:
            if order == 'desc':
                query = query.order_by(desc(order_by))
            else:
                query = query.order_by(asc(order_by))

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        return query.all()

    def exists_by_id(self, task_id: str) -> bool:
        """检查任务是否存在"""
        return self.session.query(Task).filter_by(id=task_id).first() is not None

    def bulk_save(self, tasks: List[Task]) -> List[Task]:
        """批量保存任务"""
        try:
            for task in tasks:
                self.session.add(task)
            self.session.commit()
            return tasks
        except Exception:
            self.session.rollback()
            raise

    def bulk_update_status(self, task_ids: List[str], status: TaskStatus) -> int:
        """批量更新任务状态"""
        count = 0
        for task_id in task_ids:
            if self.update_status(task_id, status):
                count += 1
        return count

    def bulk_delete(self, task_ids: List[str]) -> int:
        """批量删除任务"""
        count = 0
        for task_id in task_ids:
            if self.delete(task_id):
                count += 1
        return count

    def find_tasks_created_between(self, start_time: datetime, end_time: datetime) -> List[Task]:
        """查找指定时间范围内创建的任务"""
        return self.session.query(Task).filter(
            Task.created_at >= start_time,
            Task.created_at <= end_time
        ).all()

    def find_tasks_with_retry_count_less_than(self, max_retry_count: int) -> List[Task]:
        """查找重试次数小于指定值的任务"""
        return self.session.query(Task).filter(
            Task.retry_count < max_retry_count
        ).all()