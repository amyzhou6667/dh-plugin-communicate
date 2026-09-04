"""
DeepSeek Harness 飞书桥接插件 - Flask应用入口
"""
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timezone
import os

# 初始化数据库
db = SQLAlchemy()


def create_app(config=None):
    """创建Flask应用"""
    app = Flask(__name__)

    # 加载配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['HARNESS_BASE_URL'] = 'http://127.0.0.1:3080'
    app.config['FEISHU_APP_ID'] = ''
    app.config['FEISHU_APP_SECRET'] = ''
    app.config['BRIDGE_PORT'] = 5000
    app.config['POLL_INTERVAL_SECONDS'] = 5
    app.config['DEFAULT_TIMEOUT_SECONDS'] = 300
    app.config['MAX_RETRY_COUNT'] = 3

    # 应用自定义配置
    if config:
        app.config.update(config)

    # 初始化扩展
    db.init_app(app)
    CORS(app)

    # 注册蓝图
    from src.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from src.webhook import webhook_bp
    app.register_blueprint(webhook_bp, url_prefix='/webhook')

    # 健康检查
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0'
        })

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': '请求的资源不存在'
            },
            'message': '请求的资源不存在'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': '请求方法不允许'
            },
            'message': '请求方法不允许'
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '服务器内部错误'
            },
            'message': '服务器内部错误'
        }), 500

    # 创建数据库表
    with app.app_context():
        from src.models.task import Task
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)