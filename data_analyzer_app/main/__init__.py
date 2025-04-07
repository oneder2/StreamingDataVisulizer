# data_analyzer_app/main/__init__.py
from flask import Blueprint

# 创建蓝图实例，'main' 是蓝图名称，__name__ 帮助 Flask 找到模板和静态文件（如果在此蓝图下定义）
main_bp = Blueprint('main', __name__)

# 在末尾导入路由，避免循环导入问题
from . import routes

