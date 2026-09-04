"""
任务API模块
"""
from flask import jsonify, request
from src.api import api_bp
from src.services.api_gateway import (
    APIGateway, TaskNotFoundError, InvalidReplyError,
    InvalidRetryError, MaxRetriesExceededError, InvalidImportError
)
from src.models.task import TaskStatus
from src.app import db


@api_bp.route('/tasks/pending', methods=['GET'])
def get_pending_tasks():
    """获取待确认任务"""
    try:
        gateway = APIGateway(db.session)
        tasks = gateway.get_pending_tasks()
        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in tasks]
            },
            'message': '获取待确认任务成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '获取待确认任务失败'
        }), 500


@api_bp.route('/tasks/<task_id>/reply', methods=['POST'])
def submit_user_reply(task_id):
    """提交用户回复"""
    try:
        # 验证请求数据
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Content-Type must be application/json'
                },
                'message': '请求格式错误'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Invalid JSON format'
                },
                'message': 'JSON格式错误'
            }), 400

        # 验证必要字段
        if 'reply_text' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Missing required field: reply_text'
                },
                'message': '缺少必要字段: reply_text'
            }), 400

        if 'user_id' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Missing required field: user_id'
                },
                'message': '缺少必要字段: user_id'
            }), 400

        # 验证回复内容
        reply_text = data['reply_text']
        if not reply_text or not reply_text.strip():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'reply_text cannot be empty'
                },
                'message': '回复内容不能为空'
            }), 400

        # 提交回复
        gateway = APIGateway(db.session)
        result = gateway.submit_user_reply(
            task_id=task_id,
            reply_text=reply_text,
            user_id=data['user_id']
        )

        if result:
            # 获取更新后的任务
            task = gateway.get_task_by_id(task_id)
            return jsonify({
                'success': True,
                'data': {
                    'task_id': task_id,
                    'status': task.status.value
                },
                'message': '用户回复提交成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to submit user reply'
                },
                'message': '提交用户回复失败'
            }), 500

    except Exception as e:
        error_code = 'INTERNAL_ERROR'
        status_code = 500

        if isinstance(e, TaskNotFoundError):
            error_code = 'TASK_NOT_FOUND'
            status_code = 404
        elif isinstance(e, InvalidReplyError):
            error_code = 'INVALID_REQUEST'
            status_code = 400

        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': str(e)
            },
            'message': str(e)
        }), status_code


@api_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task_by_id(task_id):
    """根据ID获取任务"""
    try:
        gateway = APIGateway(db.session)
        task = gateway.get_task_by_id(task_id)

        if task:
            return jsonify({
                'success': True,
                'data': task.to_dict(),
                'message': '获取任务成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TASK_NOT_FOUND',
                    'message': '任务不存在'
                },
                'message': '任务不存在'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '获取任务失败'
        }), 500


@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    try:
        # 获取查询参数
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int)

        gateway = APIGateway(db.session)

        if status:
            # 验证状态参数
            try:
                task_status = TaskStatus(status)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': f'Invalid status: {status}'
                    },
                    'message': f'无效的状态: {status}'
                }), 400

            tasks = gateway.get_tasks_by_status(task_status)
        else:
            tasks = gateway.get_all_tasks()

        # 应用分页
        if offset:
            tasks = tasks[offset:]
        if limit:
            tasks = tasks[:limit]

        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in tasks]
            },
            'message': '获取任务列表成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '获取任务列表失败'
        }), 500


@api_bp.route('/tasks/<task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """更新任务状态"""
    try:
        # 验证请求数据
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Content-Type must be application/json'
                },
                'message': '请求格式错误'
            }), 400

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Missing required field: status'
                },
                'message': '缺少必要字段: status'
            }), 400

        # 验证状态参数
        try:
            status = TaskStatus(data['status'])
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': f'Invalid status: {data["status"]}'
                },
                'message': f'无效的状态: {data["status"]}'
            }), 400

        # 更新状态
        gateway = APIGateway(db.session)
        result = gateway.update_task_status(task_id, status)

        if result:
            return jsonify({
                'success': True,
                'data': {
                    'status': status.value
                },
                'message': '任务状态更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TASK_NOT_FOUND',
                    'message': '任务不存在'
                },
                'message': '任务不存在'
            }), 404

    except Exception as e:
        error_code = 'INTERNAL_ERROR'
        status_code = 500

        if isinstance(e, TaskNotFoundError):
            error_code = 'TASK_NOT_FOUND'
            status_code = 404

        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': str(e)
            },
            'message': str(e)
        }), status_code


@api_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        gateway = APIGateway(db.session)
        result = gateway.delete_task(task_id)

        if result:
            return jsonify({
                'success': True,
                'message': '任务删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TASK_NOT_FOUND',
                    'message': '任务不存在'
                },
                'message': '任务不存在'
            }), 404

    except Exception as e:
        error_code = 'INTERNAL_ERROR'
        status_code = 500

        if isinstance(e, TaskNotFoundError):
            error_code = 'TASK_NOT_FOUND'
            status_code = 404

        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': str(e)
            },
            'message': str(e)
        }), status_code


@api_bp.route('/tasks/statistics', methods=['GET'])
def get_task_statistics():
    """获取任务统计信息"""
    try:
        gateway = APIGateway(db.session)
        statistics = gateway.get_task_statistics()

        return jsonify({
            'success': True,
            'data': statistics,
            'message': '获取任务统计信息成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '获取任务统计信息失败'
        }), 500


@api_bp.route('/tasks/<task_id>/retry', methods=['POST'])
def retry_task(task_id):
    """重试任务"""
    try:
        gateway = APIGateway(db.session)
        result = gateway.retry_task(task_id)

        if result:
            task = gateway.get_task_by_id(task_id)
            return jsonify({
                'success': True,
                'data': {
                    'status': task.status.value,
                    'retry_count': task.retry_count
                },
                'message': '任务重试成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retry task'
                },
                'message': '任务重试失败'
            }), 500

    except Exception as e:
        error_code = 'INTERNAL_ERROR'
        status_code = 500

        if isinstance(e, TaskNotFoundError):
            error_code = 'TASK_NOT_FOUND'
            status_code = 404
        elif isinstance(e, InvalidRetryError):
            error_code = 'INVALID_STATUS'
            status_code = 400
        elif isinstance(e, MaxRetriesExceededError):
            error_code = 'MAX_RETRIES_EXCEEDED'
            status_code = 400

        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': str(e)
            },
            'message': str(e)
        }), status_code


@api_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    """搜索任务"""
    try:
        query = request.args.get('q', '')

        gateway = APIGateway(db.session)
        tasks = gateway.search_tasks_by_content(query)

        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in tasks]
            },
            'message': '搜索任务成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '搜索任务失败'
        }), 500


@api_bp.route('/tasks/export', methods=['GET'])
def export_tasks():
    """导出任务为JSON"""
    try:
        gateway = APIGateway(db.session)
        json_data = gateway.export_tasks_to_json()

        return json_data, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '导出任务失败'
        }), 500


@api_bp.route('/tasks/import', methods=['POST'])
def import_tasks():
    """从JSON导入任务"""
    try:
        # 验证请求数据
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Content-Type must be application/json'
                },
                'message': '请求格式错误'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Invalid JSON format'
                },
                'message': 'JSON格式错误'
            }), 400

        # 导入任务
        gateway = APIGateway(db.session)
        imported_count = gateway.import_tasks_from_json(json.dumps(data, ensure_ascii=False))

        return jsonify({
            'success': True,
            'data': {
                'imported_count': imported_count
            },
            'message': f'成功导入 {imported_count} 个任务'
        })

    except Exception as e:
        error_code = 'INTERNAL_ERROR'
        status_code = 500

        if isinstance(e, InvalidImportError):
            error_code = 'INVALID_REQUEST'
            status_code = 400

        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': str(e)
            },
            'message': str(e)
        }), status_code


@api_bp.route('/tasks/cleanup', methods=['POST'])
def cleanup_old_tasks():
    """清理旧任务"""
    try:
        # 验证请求数据
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Content-Type must be application/json'
                },
                'message': '请求格式错误'
            }), 400

        data = request.get_json()
        if not data or 'days' not in data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Missing required field: days'
                },
                'message': '缺少必要字段: days'
            }), 400

        # 验证天数参数
        try:
            days = int(data['days'])
            if days <= 0:
                raise ValueError('days must be positive')
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'days must be a positive integer'
                },
                'message': '天数必须是正整数'
            }), 400

        # 清理旧任务
        gateway = APIGateway(db.session)
        deleted_count = gateway.cleanup_old_tasks(days=days)

        return jsonify({
            'success': True,
            'data': {
                'deleted_count': deleted_count
            },
            'message': f'成功清理 {deleted_count} 个旧任务'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            },
            'message': '清理旧任务失败'
        }), 500