"""
Webhook蓝图模块
"""
from flask import Blueprint

webhook_bp = Blueprint('webhook', __name__)

from src.webhook import feishu