"""
API网关模块测试
基于接口签名契约设计测试用例
"""
import pytest
from datetime import datetime, timedelta, timezone
from src.models.task import Task, TaskStatus
from src.services.api_gateway import (
    APIGateway, TaskNotFoundError, InvalidReplyError,
    InvalidCallbackError, MessageNotFoundError, DuplicateReplyError,
    TaskTimeoutError, MaxRetriesExceededError, InvalidRetryError, InvalidImportError
)


class TestAPIGateway:
    """API网关测试"""

    def test_get_pending_tasks_success(self, db_session, sample_tasks):
        """测试获取待确认任务成功"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.PENDING
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        # 创建API网关
        gateway = APIGateway(db_session)

        # 获取待确认任务
        pending_tasks = gateway.get_pending_tasks()

        assert len(pending_tasks) == 2
        assert all(task.status == TaskStatus.PENDING for task in pending_tasks)

    def test_get_pending_tasks_empty(self, db_session):
        """测试获取待确认任务（空结果）"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)
        pending_tasks = gateway.get_pending_tasks()

        assert len(pending_tasks) == 0

    def test_get_pending_tasks_only_pending(self, db_session, sample_tasks):
        """测试只返回待确认状态的任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.REPLIED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)
        pending_tasks = gateway.get_pending_tasks()

        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == 'task_0'

    def test_submit_user_reply_success(self, db_session, sample_task):
        """测试提交用户回复成功"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务状态为已发送
        sample_task.status = TaskStatus.SENT
        sample_task.feishu_message_id = 'msg_789'

        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 提交用户回复
        result = gateway.submit_user_reply(
            task_id='task_123',
            reply_text='确认执行',
            user_id='user_456'
        )

        assert result is True

        # 验证任务状态更新
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.REPLIED
        assert task.user_reply == '确认执行'
        assert task.user_id == 'user_456'

    def test_submit_user_reply_task_not_found(self, db_session):
        """测试提交用户回复：任务不存在"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)

        # 提交不存在任务的回复
        with pytest.raises(TaskNotFoundError):
            gateway.submit_user_reply(
                task_id='non_existing_task',
                reply_text='确认执行',
                user_id='user_456'
            )

    def test_submit_user_reply_invalid_status(self, db_session, sample_task):
        """测试提交用户回复：无效任务状态"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务状态为已完成
        sample_task.status = TaskStatus.COMPLETED
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 提交已完成任务的回复
        with pytest.raises(InvalidReplyError):
            gateway.submit_user_reply(
                task_id='task_123',
                reply_text='确认执行',
                user_id='user_456'
            )

    def test_submit_user_reply_empty_reply(self, db_session, sample_task):
        """测试提交用户回复：空回复内容"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        sample_task.status = TaskStatus.SENT
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 提交空回复
        with pytest.raises(InvalidReplyError):
            gateway.submit_user_reply(
                task_id='task_123',
                reply_text='',
                user_id='user_456'
            )

    def test_submit_user_reply_whitespace_reply(self, db_session, sample_task):
        """测试提交用户回复：空白回复内容"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        sample_task.status = TaskStatus.SENT
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 提交空白回复
        with pytest.raises(InvalidReplyError):
            gateway.submit_user_reply(
                task_id='task_123',
                reply_text='   ',
                user_id='user_456'
            )

    def test_submit_user_reply_long_reply(self, db_session, sample_task):
        """测试提交用户回复：长回复内容"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        sample_task.status = TaskStatus.SENT
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 提交长回复
        long_reply = 'A' * 10000
        result = gateway.submit_user_reply(
            task_id='task_123',
            reply_text=long_reply,
            user_id='user_456'
        )

        assert result is True

        # 验证长回复
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.user_reply == long_reply

    def test_submit_user_reply_special_characters(self, db_session, sample_task):
        """测试提交用户回复：特殊字符"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        sample_task.status = TaskStatus.SENT
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 提交包含特殊字符的回复
        special_reply = '确认执行！@#$%^&*()_+{}|:"<>?'
        result = gateway.submit_user_reply(
            task_id='task_123',
            reply_text=special_reply,
            user_id='user_456'
        )

        assert result is True

        # 验证特殊字符
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.user_reply == special_reply

    def test_handle_feishu_callback_success(self, db_session, sample_task):
        """测试处理飞书回调成功"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务状态为已发送
        sample_task.status = TaskStatus.SENT
        sample_task.feishu_message_id = 'msg_789'
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 模拟飞书回调数据（使用任务ID作为message_id）
        callback_data = {
            'event': {
                'message': {
                    'content': '确认执行',
                    'message_type': 'text',
                    'open_id': 'ou_xxx',
                    'message_id': 'task_123'  # 使用任务ID
                }
            }
        }

        # 处理回调
        result = gateway.handle_feishu_callback(callback_data)

        assert result is True

        # 验证任务状态更新
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.REPLIED
        assert task.user_reply == '确认执行'
        assert task.user_id == 'ou_xxx'

    def test_handle_feishu_callback_invalid_data(self, db_session):
        """测试处理飞书回调：无效数据"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)

        # 无效回调数据
        invalid_callback_data = {
            'event': {
                'message': {
                    'content': '确认执行'
                    # 缺少必要字段
                }
            }
        }

        # 处理无效回调
        with pytest.raises(InvalidCallbackError):
            gateway.handle_feishu_callback(invalid_callback_data)

    def test_handle_feishu_callback_message_not_found(self, db_session):
        """测试处理飞书回调：消息不存在"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)

        # 回调数据中的消息ID不存在
        callback_data = {
            'event': {
                'message': {
                    'content': '确认执行',
                    'message_type': 'text',
                    'open_id': 'ou_xxx',
                    'message_id': 'non_existing_msg_id'
                }
            }
        }

        # 处理不存在的消息回调
        with pytest.raises(MessageNotFoundError):
            gateway.handle_feishu_callback(callback_data)

    def test_handle_feishu_callback_duplicate_reply(self, db_session, sample_task):
        """测试处理飞书回调：重复回复"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务状态为已回复
        sample_task.status = TaskStatus.REPLIED
        sample_task.feishu_message_id = 'msg_789'
        sample_task.user_reply = '原始回复'
        sample_task.user_id = 'user_original'
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 模拟重复回复（使用任务ID作为message_id）
        callback_data = {
            'event': {
                'message': {
                    'content': '新回复',
                    'message_type': 'text',
                    'open_id': 'ou_xxx',
                    'message_id': 'task_123'  # 使用任务ID
                }
            }
        }

        # 处理重复回复（应该失败）
        with pytest.raises(DuplicateReplyError):
            gateway.handle_feishu_callback(callback_data)

    def test_handle_feishu_callback_timeout_task(self, db_session, sample_task):
        """测试处理飞书回调：超时任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务为超时状态
        sample_task.status = TaskStatus.TIMEOUT
        sample_task.feishu_message_id = 'msg_789'
        sample_task.timeout_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 模拟超时任务的回复（使用任务ID作为message_id）
        callback_data = {
            'event': {
                'message': {
                    'content': '确认执行',
                    'message_type': 'text',
                    'open_id': 'ou_xxx',
                    'message_id': 'task_123'  # 使用任务ID
                }
            }
        }

        # 处理超时任务回复（应该失败）
        with pytest.raises(TaskTimeoutError):
            gateway.handle_feishu_callback(callback_data)

    def test_get_task_by_id(self, db_session, sample_task):
        """测试根据ID获取任务"""
        from src.services.api_gateway import APIGateway

        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)
        task = gateway.get_task_by_id('task_123')

        assert task is not None
        assert task.id == 'task_123'

    def test_get_task_by_id_not_found(self, db_session):
        """测试根据ID获取任务：任务不存在"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)
        task = gateway.get_task_by_id('non_existing_task')

        assert task is None

    def test_get_tasks_by_status(self, db_session, sample_tasks):
        """测试根据状态获取任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.PENDING

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 获取待确认任务
        pending_tasks = gateway.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending_tasks) == 2

        # 获取已发送任务
        sent_tasks = gateway.get_tasks_by_status(TaskStatus.SENT)
        assert len(sent_tasks) == 1

    def test_get_tasks_by_status_empty(self, db_session):
        """测试根据状态获取任务：空结果"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        gateway = APIGateway(db_session)
        tasks = gateway.get_tasks_by_status(TaskStatus.PENDING)

        assert len(tasks) == 0

    def test_get_timeout_tasks(self, db_session, sample_tasks):
        """测试获取超时任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置超时任务
        sample_tasks[0].timeout_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        sample_tasks[0].status = TaskStatus.SENT

        sample_tasks[1].timeout_at = datetime.now(timezone.utc) + timedelta(seconds=300)
        sample_tasks[1].status = TaskStatus.SENT

        sample_tasks[2].timeout_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)
        timeout_tasks = gateway.get_timeout_tasks()

        assert len(timeout_tasks) == 1
        assert timeout_tasks[0].id == 'task_0'

    def test_get_timeout_tasks_empty(self, db_session):
        """测试获取超时任务：空结果"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)
        timeout_tasks = gateway.get_timeout_tasks()

        assert len(timeout_tasks) == 0

    def test_update_task_status(self, db_session, sample_task):
        """测试更新任务状态"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 更新状态
        result = gateway.update_task_status('task_123', TaskStatus.SENT)

        assert result is True

        # 验证更新
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.SENT

    def test_update_task_status_not_found(self, db_session):
        """测试更新任务状态：任务不存在"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        gateway = APIGateway(db_session)

        # 更新不存在任务的状态
        with pytest.raises(TaskNotFoundError):
            gateway.update_task_status('non_existing_task', TaskStatus.SENT)

    def test_delete_task(self, db_session, sample_task):
        """测试删除任务"""
        from src.services.api_gateway import APIGateway

        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 删除任务
        result = gateway.delete_task('task_123')

        assert result is True

        # 验证删除
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task is None

    def test_delete_task_not_found(self, db_session):
        """测试删除任务：任务不存在"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)

        # 删除不存在的任务
        with pytest.raises(TaskNotFoundError):
            gateway.delete_task('non_existing_task')

    def test_get_task_statistics(self, db_session, sample_tasks):
        """测试获取任务统计信息"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)
        statistics = gateway.get_task_statistics()

        assert statistics['total'] == 3
        assert statistics['pending'] == 1
        assert statistics['sent'] == 1
        assert statistics['completed'] == 1
        assert statistics['replied'] == 0
        assert statistics['timeout'] == 0
        assert statistics['failed'] == 0

    def test_get_task_statistics_empty(self, db_session):
        """测试获取任务统计信息：空数据库"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)
        statistics = gateway.get_task_statistics()

        assert statistics['total'] == 0
        assert statistics['pending'] == 0
        assert statistics['sent'] == 0
        assert statistics['completed'] == 0
        assert statistics['replied'] == 0
        assert statistics['timeout'] == 0
        assert statistics['failed'] == 0

    def test_retry_task(self, db_session, sample_task):
        """测试重试任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务为失败状态
        sample_task.status = TaskStatus.FAILED
        sample_task.retry_count = 2
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 重试任务
        result = gateway.retry_task('task_123')

        assert result is True

        # 验证重试
        task = db_session.query(Task).filter_by(id='task_123').first()
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 3

    def test_retry_task_not_found(self, db_session):
        """测试重试任务：任务不存在"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)

        # 重试不存在的任务
        with pytest.raises(TaskNotFoundError):
            gateway.retry_task('non_existing_task')

    def test_retry_task_max_retries_exceeded(self, db_session, sample_task, sample_config):
        """测试重试任务：超过最大重试次数"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务超过最大重试次数
        sample_task.status = TaskStatus.FAILED
        sample_task.retry_count = sample_config.max_retry_count
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 尝试重试（应该失败）
        with pytest.raises(MaxRetriesExceededError):
            gateway.retry_task('task_123')

    def test_retry_task_invalid_status(self, db_session, sample_task):
        """测试重试任务：无效任务状态"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置任务为已完成状态
        sample_task.status = TaskStatus.COMPLETED
        db_session.add(sample_task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 尝试重试已完成任务（应该失败）
        with pytest.raises(InvalidRetryError):
            gateway.retry_task('task_123')

    def test_search_tasks_by_content(self, db_session, sample_tasks):
        """测试按内容搜索任务"""
        from src.services.api_gateway import APIGateway

        # 设置不同内容
        sample_tasks[0].content = '删除用户数据'
        sample_tasks[1].content = '修改用户权限'
        sample_tasks[2].content = '删除系统配置'

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 搜索包含"删除"的任务
        tasks = gateway.search_tasks_by_content('删除')

        assert len(tasks) == 2
        assert tasks[0].id == 'task_0'
        assert tasks[1].id == 'task_2'

    def test_search_tasks_by_content_no_match(self, db_session, sample_tasks):
        """测试按内容搜索任务：无匹配"""
        from src.services.api_gateway import APIGateway

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 搜索不存在的内容
        tasks = gateway.search_tasks_by_content('不存在的内容')

        assert len(tasks) == 0

    def test_search_tasks_by_content_empty_query(self, db_session, sample_tasks):
        """测试按内容搜索任务：空查询"""
        from src.services.api_gateway import APIGateway

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 空查询应该返回所有任务
        tasks = gateway.search_tasks_by_content('')

        assert len(tasks) == 3

    def test_export_tasks_to_json(self, db_session, sample_tasks):
        """测试导出任务为JSON"""
        from src.services.api_gateway import APIGateway
        import json

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 导出任务
        json_data = gateway.export_tasks_to_json()

        # 验证JSON格式
        data = json.loads(json_data)
        assert len(data) == 3
        assert data[0]['id'] == 'task_0'
        assert data[1]['id'] == 'task_1'
        assert data[2]['id'] == 'task_2'

    def test_export_tasks_to_json_empty(self, db_session):
        """测试导出任务为JSON：空数据库"""
        from src.services.api_gateway import APIGateway
        import json

        gateway = APIGateway(db_session)

        # 导出空任务列表
        json_data = gateway.export_tasks_to_json()

        # 验证JSON格式
        data = json.loads(json_data)
        assert len(data) == 0

    def test_import_tasks_from_json(self, db_session):
        """测试从JSON导入任务"""
        from src.services.api_gateway import APIGateway
        import json

        # 准备JSON数据
        tasks_data = [
            {
                'id': 'imported_task_1',
                'harness_task_id': 'harness_1',
                'content': '导入任务1',
                'context': {'key': 'value'},
                'status': 'pending'
            },
            {
                'id': 'imported_task_2',
                'harness_task_id': 'harness_2',
                'content': '导入任务2',
                'context': {},
                'status': 'pending'
            }
        ]
        json_data = json.dumps(tasks_data)

        gateway = APIGateway(db_session)

        # 导入任务
        imported_count = gateway.import_tasks_from_json(json_data)

        assert imported_count == 2

        # 验证导入
        tasks = gateway.get_all_tasks()
        assert len(tasks) == 2
        assert tasks[0].id == 'imported_task_1'
        assert tasks[1].id == 'imported_task_2'

    def test_import_tasks_from_json_invalid_format(self, db_session):
        """测试从JSON导入任务：无效格式"""
        from src.services.api_gateway import APIGateway

        gateway = APIGateway(db_session)

        # 无效JSON格式
        with pytest.raises(InvalidImportError):
            gateway.import_tasks_from_json('invalid json')

    def test_import_tasks_from_json_missing_fields(self, db_session):
        """测试从JSON导入任务：缺少字段"""
        from src.services.api_gateway import APIGateway
        import json

        # 缺少必要字段
        tasks_data = [
            {
                'id': 'imported_task_1'
                # 缺少harness_task_id, content等
            }
        ]
        json_data = json.dumps(tasks_data)

        gateway = APIGateway(db_session)

        # 导入缺少字段的任务（应该失败）
        with pytest.raises(InvalidImportError):
            gateway.import_tasks_from_json(json_data)

    def test_cleanup_old_tasks(self, db_session, sample_tasks):
        """测试清理旧任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置不同的创建时间
        sample_tasks[0].created_at = datetime.now(timezone.utc) - timedelta(days=30)
        sample_tasks[0].status = TaskStatus.COMPLETED

        sample_tasks[1].created_at = datetime.now(timezone.utc) - timedelta(days=15)
        sample_tasks[1].status = TaskStatus.COMPLETED

        sample_tasks[2].created_at = datetime.now(timezone.utc) - timedelta(days=5)
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 清理30天前的任务
        deleted_count = gateway.cleanup_old_tasks(days=30)

        assert deleted_count == 1

        # 验证清理
        remaining_tasks = gateway.get_all_tasks()
        assert len(remaining_tasks) == 2

    def test_cleanup_old_tasks_no_old_tasks(self, db_session, sample_tasks):
        """测试清理旧任务：没有旧任务"""
        from src.services.api_gateway import APIGateway

        # 设置所有任务为最近创建
        for task in sample_tasks:
            task.created_at = datetime.now(timezone.utc) - timedelta(days=5)
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 清理30天前的任务
        deleted_count = gateway.cleanup_old_tasks(days=30)

        assert deleted_count == 0

        # 验证没有任务被删除
        remaining_tasks = gateway.get_all_tasks()
        assert len(remaining_tasks) == 3

    def test_cleanup_old_tasks_keep_recent(self, db_session, sample_tasks):
        """测试清理旧任务：保留最近任务"""
        from src.services.api_gateway import APIGateway
        from src.models.task import TaskStatus

        # 设置不同的创建时间和状态（使用 naive datetime 以兼容 SQLite）
        sample_tasks[0].created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        sample_tasks[0].status = TaskStatus.COMPLETED

        sample_tasks[1].created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=15)
        sample_tasks[1].status = TaskStatus.PENDING  # 待处理任务

        sample_tasks[2].created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=5)
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        gateway = APIGateway(db_session)

        # 清理30天前的已完成任务
        deleted_count = gateway.cleanup_old_tasks(days=30, status=TaskStatus.COMPLETED)

        assert deleted_count == 1

        # 验证清理
        remaining_tasks = gateway.get_all_tasks()
        assert len(remaining_tasks) == 2
        assert remaining_tasks[0].id == 'task_1'
        assert remaining_tasks[1].id == 'task_2'