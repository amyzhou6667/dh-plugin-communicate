"""
飞书Webhook模块
"""
from flask import jsonify, request
from src.webhook import webhook_bp
from src.services.api_gateway import (
    APIGateway, InvalidCallbackError, MessageNotFoundError,
    DuplicateReplyError, TaskTimeoutError
)
from src.app import db


@webhook_bp.route('/feishu', methods=['POST'])
def handle_feishu_callback():
    """处理飞书回调"""
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

        # 处理回调
        gateway = APIGateway(db.session)
        result = gateway.handle_feishu_callback(data)

        if result:
            return jsonify({
                'success': True,
                'message': '回调处理成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to handle callback'
                },
                'message': '回调处理失败'
            }), 500

    except Exception as e:
        error_code = 'INTERNAL_ERROR'
        status_code = 500

        if isinstance(e, InvalidCallbackError):
            error_code = 'INVALID_REQUEST'
            status_code = 400
        elif isinstance(e, MessageNotFoundError):
            error_code = 'MESSAGE_NOT_FOUND'
            status_code = 404
        elif isinstance(e, DuplicateReplyError):
            error_code = 'DUPLICATE_REPLY'
            status_code = 400
        elif isinstance(e, TaskTimeoutError):
            error_code = 'TASK_TIMEOUT'
            status_code = 400

        return jsonify({
            'success': False,
            'error': {
                'code': error_code,
                'message': str(e)
            },
            'message': str(e)
        }), status_code