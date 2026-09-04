"""
API蓝图模块
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from src.api import tasks