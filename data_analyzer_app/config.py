# data_analyzer_app/config.py
import os

# 获取应用包的根目录
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_that_should_be_changed'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024 # 32 MB upload limit
    # 可以添加其他通用配置

    @staticmethod
    def init_app(app):
        # 执行应用初始化相关的配置
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境可能需要更安全的密钥管理和不同的上传路径等
    SECRET_KEY = os.environ.get('SECRET_KEY') # 必须从环境变量获取


# 配置字典，方便工厂函数根据名称加载
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig # 默认使用开发配置
}

# 注意: 如果使用这个文件，需要在 data_analyzer_app/__init__.py 中修改配置加载方式：
# from .config import config
# ...
# app.config.from_object(config[config_name])
# config[config_name].init_app(app)
# 并且移除 __init__.py 中的 UPLOAD_FOLDER 和 SECRET_KEY 的直接设置。
# 目前为了简单，__init__.py 中是直接设置的，你可以根据需要切换。

