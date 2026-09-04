"""
测试配置文件
提供测试夹具和通用测试工具
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta, timezone


@pytest.fixture
def app():
    """创建测试用的Flask应用"""
    from src.app import create_app

    # 使用临时数据库
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        'TESTING': True,
        'DATABASE_URL': f'sqlite:///{db_path}',
        'HARNESS_BASE_URL': 'http://127.0.0.1:3080',
        'FEISHU_APP_ID': 'test_app_id',
        'FEISHU_APP_SECRET': 'test_app_secret',
        'BRIDGE_PORT': 5000,
        'POLL_INTERVAL_SECONDS': 5,
        'DEFAULT_TIMEOUT_SECONDS': 300,
        'MAX_RETRY_COUNT': 3
    })

    yield app

    # 清理
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建测试CLI运行器"""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """创建测试数据库会话"""
    from src.models import db

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def sample_task():
    """创建示例任务对象"""
    from src.models.task import Task, TaskStatus

    return Task(
        id='task_123',
        harness_task_id='harness_456',
        content='请确认以下操作：删除用户数据',
        context={'user_id': 'user_789', 'action': 'delete_user_data'},
        status=TaskStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        timeout_at=datetime.now(timezone.utc) + timedelta(seconds=300),
        retry_count=0
    )


@pytest.fixture
def sample_tasks():
    """创建多个示例任务对象"""
    from src.models.task import Task, TaskStatus

    tasks = []
    for i in range(3):
        task = Task(
            id=f'task_{i}',
            harness_task_id=f'harness_{i}',
            content=f'任务内容 {i}',
            context={'index': i},
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            timeout_at=datetime.now(timezone.utc) + timedelta(seconds=300),
            retry_count=0
        )
        tasks.append(task)

    return tasks


@pytest.fixture
def sample_config():
    """创建示例配置对象"""
    from src.config import Config

    return Config(
        harness_base_url='http://127.0.0.1:3080',
        harness_api_key=None,
        feishu_app_id='test_app_id',
        feishu_app_secret='test_app_secret',
        feishu_encrypt_key=None,
        feishu_verification_token=None,
        bridge_port=5000,
        poll_interval_seconds=5,
        default_timeout_seconds=300,
        max_retry_count=3,
        database_url='sqlite:///:memory:'
    )