# run.py
import os
from data_analyzer_app import create_app # 从应用包导入 create_app 工厂函数

# 创建 Flask 应用实例 (可以传递配置名称，例如 'development' 或 'production')
# config_name = os.getenv('FLASK_CONFIG') or 'default' # Example using environment variable
app = create_app() # Using default config defined in factory for now

# 运行 Flask 开发服务器
if __name__ == '__main__':
    # host='0.0.0.0' 使其在网络上可访问
    # debug=True 启用调试模式和自动重载 (生产环境应禁用)
    # 生产环境推荐使用 Gunicorn, Waitress 等 WSGI 服务器
    app.run(host='0.0.0.0', port=5000, debug=True)

