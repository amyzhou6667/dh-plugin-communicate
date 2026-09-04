"""
任务数据模型
"""
from datetime import datetime, timezone
from enum import Enum
from src.app import db


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = 'pending'  # 待确认
    SENT = 'sent'  # 已发送飞书
    REPLIED = 'replied'  # 已回复
    COMPLETED = 'completed'  # 已完成
    TIMEOUT = 'timeout'  # 超时
    FAILED = 'failed'  # 失败


class Task(db.Model):
    """任务模型"""
    __tablename__ = 'tasks'

    id = db.Column(db.String(50), primary_key=True)
    harness_task_id = db.Column(db.String(100), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    context = db.Column(db.JSON, nullable=True)
    status = db.Column(db.Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)
    feishu_message_id = db.Column(db.String(100), nullable=True)
    user_reply = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    timeout_at = db.Column(db.DateTime, nullable=True, index=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'harness_task_id': self.harness_task_id,
            'content': self.content,
            'context': self.context,
            'status': self.status.value,
            'feishu_message_id': self.feishu_message_id,
            'user_reply': self.user_reply,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'timeout_at': self.timeout_at.isoformat() if self.timeout_at else None,
            'retry_count': self.retry_count
        }

    def __repr__(self):
        return f'<Task {self.id}>'


class UserReply:
    """用户回复实体"""

    def __init__(self, task_id: str, reply_text: str, user_id: str, replied_at: datetime = None):
        self.task_id = task_id
        self.reply_text = reply_text
        self.user_id = user_id
        self.replied_at = replied_at or datetime.now(timezone.utc)

    def to_dict(self):
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'reply_text': self.reply_text,
            'user_id': self.user_id,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None
        }

    def __repr__(self):
        return f'<UserReply task_id={self.task_id}>'