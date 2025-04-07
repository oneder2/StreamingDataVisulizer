# data_analyzer_app/__init__.py
import os
import logging
from flask import Flask

# 导入蓝图
from .main.routes import main_bp
from .analysis.routes import analysis_bp
# 导入配置 (如果使用 config.py)
# from .config import config # Example

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__,
                static_folder='static', # 相对于应用包根目录
                # template_folder='templates' # 如果使用模板
               )

    # --- 配置 ---
    # 可以根据 config_name 加载不同配置
    # app.config.from_object(config[config_name]) # Example
    # 简单的配置方式：
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads') # uploads 文件夹将在 app 包内
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # Example: Limit upload size to 32MB
    # 确保设置 SECRET_KEY，即使现在没用到 session
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'a_default_secret_key_for_dev'


    # --- 日志设置 ---
    log_level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app.logger.setLevel(log_level)
    app.logger.info(f"Flask app created with log level {log_level}")


    # --- 确保上传文件夹存在 ---
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        app.logger.info(f"Upload folder checked/created: {app.config['UPLOAD_FOLDER']}")
    except OSError as e:
         app.logger.error(f"Could not create upload folder: {app.config['UPLOAD_FOLDER']}, Error: {e}")


    # --- 注册蓝图 ---
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp, url_prefix='/analyze') # 给分析路由加个前缀 (可选)
    app.logger.info("Blueprints registered (main_bp: /, analysis_bp: /analyze)")


    # --- 其他扩展初始化 (例如数据库 SQLAlchemy, 登录 LoginManager) ---
    # db.init_app(app)
    # login_manager.init_app(app)


    # --- 返回应用实例 ---
    return app

