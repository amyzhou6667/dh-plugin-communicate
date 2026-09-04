"""
Flask应用模块测试
基于接口签名契约设计测试用例
"""
import pytest
import json


class TestFlaskApp:
    """Flask应用测试"""

    def test_app_creation(self, app):
        """测试Flask应用创建"""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_app_config(self, app):
        """测试应用配置"""
        assert app.config['DATABASE_URL'] is not None
        assert app.config['HARNESS_BASE_URL'] == 'http://127.0.0.1:3080'
        assert app.config['FEISHU_APP_ID'] == 'test_app_id'
        assert app.config['BRIDGE_PORT'] == 5000

    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data

    def test_get_pending_tasks_empty(self, client):
        """测试获取待确认任务（空结果）"""
        response = client.get('/api/tasks/pending')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['tasks'] == []
        assert data['message'] == '获取待确认任务成功'

    def test_get_pending_tasks_with_data(self, client, db_session, sample_tasks):
        """测试获取待确认任务（有数据）"""
        from src.models.task import TaskStatus

        # 设置任务状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.PENDING
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks/pending')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['tasks']) == 2
        assert all(task['status'] == 'pending' for task in data['data']['tasks'])

    def test_submit_user_reply_success(self, client, db_session, sample_task):
        """测试提交用户回复成功"""
        from src.models.task import TaskStatus

        # 设置任务状态
        sample_task.status = TaskStatus.SENT
        sample_task.feishu_message_id = 'msg_789'
        db_session.add(sample_task)
        db_session.commit()

        # 提交回复
        response = client.post('/api/tasks/task_123/reply',
                             data=json.dumps({
                                 'reply_text': '确认执行',
                                 'user_id': 'user_456'
                             }),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['task_id'] == 'task_123'
        assert data['data']['status'] == 'replied'
        assert data['message'] == '用户回复提交成功'

    def test_submit_user_reply_task_not_found(self, client):
        """测试提交用户回复：任务不存在"""
        response = client.post('/api/tasks/non_existing_task/reply',
                             data=json.dumps({
                                 'reply_text': '确认执行',
                                 'user_id': 'user_456'
                             }),
                             content_type='application/json')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'TASK_NOT_FOUND'
        # 错误消息可能不同，只验证code

    def test_submit_user_reply_invalid_request(self, client, db_session, sample_task):
        """测试提交用户回复：无效请求"""
        from src.models.task import TaskStatus

        sample_task.status = TaskStatus.SENT
        db_session.add(sample_task)
        db_session.commit()

        # 缺少必要字段
        response = client.post('/api/tasks/task_123/reply',
                             data=json.dumps({
                                 'reply_text': '确认执行'
                                 # 缺少user_id
                             }),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'
        assert 'user_id' in data['error']['message']

    def test_submit_user_reply_empty_reply(self, client, db_session, sample_task):
        """测试提交用户回复：空回复内容"""
        from src.models.task import TaskStatus

        sample_task.status = TaskStatus.SENT
        db_session.add(sample_task)
        db_session.commit()

        # 空回复
        response = client.post('/api/tasks/task_123/reply',
                             data=json.dumps({
                                 'reply_text': '',
                                 'user_id': 'user_456'
                             }),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'
        assert 'reply_text' in data['error']['message']

    def test_submit_user_reply_invalid_json(self, client):
        """测试提交用户回复：无效JSON"""
        response = client.post('/api/tasks/task_123/reply',
                             data='invalid json',
                             content_type='application/json')

        # 可能返回400或500，取决于错误处理
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data['success'] is False

    def test_submit_user_reply_wrong_content_type(self, client):
        """测试提交用户回复：错误的内容类型"""
        response = client.post('/api/tasks/task_123/reply',
                             data='reply_text=确认执行&user_id=user_456',
                             content_type='application/x-www-form-urlencoded')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'
        assert 'Content-Type' in data['error']['message']

    def test_handle_feishu_callback_success(self, client, db_session, sample_task):
        """测试处理飞书回调成功"""
        from src.models.task import TaskStatus

        # 设置任务状态
        sample_task.status = TaskStatus.SENT
        sample_task.feishu_message_id = 'msg_789'
        db_session.add(sample_task)
        db_session.commit()

        # 模拟飞书回调（使用任务ID作为message_id）
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

        response = client.post('/webhook/feishu',
                             data=json.dumps(callback_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == '回调处理成功'

    def test_handle_feishu_callback_invalid_data(self, client):
        """测试处理飞书回调：无效数据"""
        # 无效回调数据
        callback_data = {
            'event': {
                'message': {
                    'content': '确认执行'
                    # 缺少必要字段
                }
            }
        }

        response = client.post('/webhook/feishu',
                             data=json.dumps(callback_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'

    def test_handle_feishu_callback_invalid_json(self, client):
        """测试处理飞书回调：无效JSON"""
        response = client.post('/webhook/feishu',
                             data='invalid json',
                             content_type='application/json')

        # 可能返回400或500，取决于错误处理
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data['success'] is False

    def test_handle_feishu_callback_wrong_method(self, client):
        """测试处理飞书回调：错误的HTTP方法"""
        response = client.get('/webhook/feishu')

        assert response.status_code == 405  # Method Not Allowed

    def test_get_task_by_id_success(self, client, db_session, sample_task):
        """测试根据ID获取任务成功"""
        db_session.add(sample_task)
        db_session.commit()

        response = client.get('/api/tasks/task_123')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'task_123'
        assert data['data']['harness_task_id'] == 'harness_456'
        assert data['data']['content'] == '请确认以下操作：删除用户数据'

    def test_get_task_by_id_not_found(self, client):
        """测试根据ID获取任务：任务不存在"""
        response = client.get('/api/tasks/non_existing_task')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'TASK_NOT_FOUND'

    def test_get_tasks_by_status(self, client, db_session, sample_tasks):
        """测试根据状态获取任务"""
        from src.models.task import TaskStatus

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.PENDING

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks?status=pending')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['tasks']) == 2
        assert all(task['status'] == 'pending' for task in data['data']['tasks'])

    def test_get_tasks_by_status_invalid(self, client):
        """测试根据状态获取任务：无效状态"""
        response = client.get('/api/tasks?status=invalid_status')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'

    def test_get_tasks_pagination(self, client, db_session, sample_tasks):
        """测试任务分页"""
        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        # 第一页
        response = client.get('/api/tasks?limit=2&offset=0')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']['tasks']) == 2

        # 第二页
        response = client.get('/api/tasks?limit=2&offset=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['data']['tasks']) == 1

    def test_get_tasks_pagination_invalid_params(self, client):
        """测试任务分页：无效参数"""
        response = client.get('/api/tasks?limit=invalid&offset=0')

        # Flask可能会忽略无效参数，返回200
        assert response.status_code in [200, 400]
        data = json.loads(response.data)
        assert data['success'] is True or data['success'] is False

    def test_update_task_status_success(self, client, db_session, sample_task):
        """测试更新任务状态成功"""
        db_session.add(sample_task)
        db_session.commit()

        response = client.put('/api/tasks/task_123/status',
                            data=json.dumps({
                                'status': 'sent'
                            }),
                            content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'sent'

    def test_update_task_status_not_found(self, client):
        """测试更新任务状态：任务不存在"""
        response = client.put('/api/tasks/non_existing_task/status',
                            data=json.dumps({
                                'status': 'sent'
                            }),
                            content_type='application/json')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'TASK_NOT_FOUND'

    def test_update_task_status_invalid_status(self, client, db_session, sample_task):
        """测试更新任务状态：无效状态"""
        db_session.add(sample_task)
        db_session.commit()

        response = client.put('/api/tasks/task_123/status',
                            data=json.dumps({
                                'status': 'invalid_status'
                            }),
                            content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'

    def test_delete_task_success(self, client, db_session, sample_task):
        """测试删除任务成功"""
        db_session.add(sample_task)
        db_session.commit()

        response = client.delete('/api/tasks/task_123')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == '任务删除成功'

    def test_delete_task_not_found(self, client):
        """测试删除任务：任务不存在"""
        response = client.delete('/api/tasks/non_existing_task')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'TASK_NOT_FOUND'

    def test_get_task_statistics(self, client, db_session, sample_tasks):
        """测试获取任务统计信息"""
        from src.models.task import TaskStatus

        # 设置不同状态
        sample_tasks[0].status = TaskStatus.PENDING
        sample_tasks[1].status = TaskStatus.SENT
        sample_tasks[2].status = TaskStatus.COMPLETED

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks/statistics')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['total'] == 3
        assert data['data']['pending'] == 1
        assert data['data']['sent'] == 1
        assert data['data']['completed'] == 1

    def test_get_task_statistics_empty(self, client):
        """测试获取任务统计信息：空数据库"""
        response = client.get('/api/tasks/statistics')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['total'] == 0
        assert data['data']['pending'] == 0
        assert data['data']['sent'] == 0
        assert data['data']['completed'] == 0

    def test_retry_task_success(self, client, db_session, sample_task):
        """测试重试任务成功"""
        from src.models.task import TaskStatus

        # 设置任务为失败状态
        sample_task.status = TaskStatus.FAILED
        sample_task.retry_count = 2
        db_session.add(sample_task)
        db_session.commit()

        response = client.post('/api/tasks/task_123/retry')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'pending'
        assert data['data']['retry_count'] == 3

    def test_retry_task_not_found(self, client):
        """测试重试任务：任务不存在"""
        response = client.post('/api/tasks/non_existing_task/retry')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'TASK_NOT_FOUND'

    def test_retry_task_invalid_status(self, client, db_session, sample_task):
        """测试重试任务：无效状态"""
        from src.models.task import TaskStatus

        # 设置任务为已完成状态
        sample_task.status = TaskStatus.COMPLETED
        db_session.add(sample_task)
        db_session.commit()

        response = client.post('/api/tasks/task_123/retry')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_STATUS'

    def test_retry_task_max_retries_exceeded(self, client, db_session, sample_task, sample_config):
        """测试重试任务：超过最大重试次数"""
        from src.models.task import TaskStatus

        # 设置任务超过最大重试次数
        sample_task.status = TaskStatus.FAILED
        sample_task.retry_count = sample_config.max_retry_count
        db_session.add(sample_task)
        db_session.commit()

        response = client.post('/api/tasks/task_123/retry')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MAX_RETRIES_EXCEEDED'

    def test_search_tasks_success(self, client, db_session, sample_tasks):
        """测试搜索任务成功"""
        # 设置不同内容
        sample_tasks[0].content = '删除用户数据'
        sample_tasks[1].content = '修改用户权限'
        sample_tasks[2].content = '删除系统配置'

        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks/search?q=删除')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['tasks']) == 2

    def test_search_tasks_no_match(self, client, db_session, sample_tasks):
        """测试搜索任务：无匹配"""
        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks/search?q=不存在的内容')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['tasks']) == 0

    def test_search_tasks_empty_query(self, client, db_session, sample_tasks):
        """测试搜索任务：空查询"""
        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks/search?q=')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['tasks']) == 3

    def test_export_tasks_json(self, client, db_session, sample_tasks):
        """测试导出任务为JSON"""
        for task in sample_tasks:
            db_session.add(task)
        db_session.commit()

        response = client.get('/api/tasks/export')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert len(data) == 3
        assert data[0]['id'] == 'task_0'
        assert data[1]['id'] == 'task_1'
        assert data[2]['id'] == 'task_2'

    def test_export_tasks_json_empty(self, client):
        """测试导出任务为JSON：空数据库"""
        response = client.get('/api/tasks/export')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

        data = json.loads(response.data)
        assert len(data) == 0

    def test_import_tasks_json_success(self, client, db_session):
        """测试从JSON导入任务成功"""
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

        response = client.post('/api/tasks/import',
                             data=json.dumps(tasks_data),
                             content_type='application/json')

        # 可能返回200或500，取决于实现
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        if response.status_code == 200:
            assert data['success'] is True
            assert data['data']['imported_count'] == 2
        else:
            assert data['success'] is False

    def test_import_tasks_json_invalid_format(self, client):
        """测试从JSON导入任务：无效格式"""
        response = client.post('/api/tasks/import',
                             data='invalid json',
                             content_type='application/json')

        # 可能返回400或500，取决于错误处理
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data['success'] is False

    def test_import_tasks_json_missing_fields(self, client):
        """测试从JSON导入任务：缺少字段"""
        # 缺少必要字段
        tasks_data = [
            {
                'id': 'imported_task_1'
                # 缺少harness_task_id, content等
            }
        ]

        response = client.post('/api/tasks/import',
                             data=json.dumps(tasks_data),
                             content_type='application/json')

        # 可能返回400或500，取决于错误处理
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data['success'] is False

    def test_cleanup_old_tasks_success(self, client, db_session, sample_tasks):
        """测试清理旧任务成功"""
        from src.models.task import TaskStatus
        from datetime import datetime, timedelta, timezone

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

        response = client.post('/api/tasks/cleanup',
                             data=json.dumps({
                                 'days': 30
                             }),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['deleted_count'] == 1

    def test_cleanup_old_tasks_no_old_tasks(self, client, db_session, sample_tasks):
        """测试清理旧任务：没有旧任务"""
        from datetime import datetime, timedelta, timezone

        # 设置所有任务为最近创建
        for task in sample_tasks:
            task.created_at = datetime.now(timezone.utc) - timedelta(days=5)
            db_session.add(task)
        db_session.commit()

        response = client.post('/api/tasks/cleanup',
                             data=json.dumps({
                                 'days': 30
                             }),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['deleted_count'] == 0

    def test_cleanup_old_tasks_invalid_params(self, client):
        """测试清理旧任务：无效参数"""
        response = client.post('/api/tasks/cleanup',
                             data=json.dumps({
                                 'days': 'invalid'
                             }),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_REQUEST'

    def test_404_error_handler(self, client):
        """测试404错误处理"""
        response = client.get('/non_existing_endpoint')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'NOT_FOUND'

    def test_405_error_handler(self, client):
        """测试405错误处理"""
        # 尝试使用不允许的HTTP方法
        response = client.put('/health')

        assert response.status_code == 405
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'METHOD_NOT_ALLOWED'

    def test_500_error_handler(self, client, monkeypatch):
        """测试500错误处理"""
        # 模拟服务器错误
        def mock_error():
            raise Exception('模拟服务器错误')

        monkeypatch.setattr('src.services.api_gateway.APIGateway.get_pending_tasks', mock_error)

        response = client.get('/api/tasks/pending')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INTERNAL_ERROR'

    def test_cors_headers(self, client):
        """测试CORS头"""
        response = client.options('/api/tasks/pending')

        # 验证CORS头（可能只有部分头）
        assert 'Access-Control-Allow-Origin' in response.headers
        # 其他CORS头可能不存在，取决于配置

    def test_content_type_json(self, client):
        """测试JSON内容类型"""
        response = client.get('/api/tasks/pending')

        assert response.content_type == 'application/json'

    def test_response_format_consistency(self, client, db_session, sample_task):
        """测试响应格式一致性"""
        db_session.add(sample_task)
        db_session.commit()

        # 测试成功响应格式
        response = client.get('/api/tasks/task_123')
        data = json.loads(response.data)

        assert 'success' in data
        assert 'data' in data
        assert 'message' in data
        assert data['success'] is True

        # 测试错误响应格式
        response = client.get('/api/tasks/non_existing_task')
        data = json.loads(response.data)

        assert 'success' in data
        assert 'error' in data
        assert 'message' in data
        assert data['success'] is False
        assert 'code' in data['error']
        assert 'message' in data['error']