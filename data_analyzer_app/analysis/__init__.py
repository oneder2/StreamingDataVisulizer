# data_analyzer_app/analysis/__init__.py
from flask import Blueprint

# url_prefix='/analyze' 将使此蓝图下的所有路由都以 /analyze 开头
analysis_bp = Blueprint('analysis', __name__, url_prefix='/analyze')

# 在末尾导入路由，避免循环导入
from . import routes

