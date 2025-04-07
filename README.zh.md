# DATA-THONE: 音乐数据分析与可视化平台

[English](README.md) | [简体中文](README.zh.md)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/) [![Flask](https://img.shields.io/badge/Flask-2.x%2B-green.svg)](https://flask.palletsprojects.com/) [![Pandas](https://img.shields.io/badge/Pandas-1.x%2B-yellow.svg)](https://pandas.pydata.org/) [![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-blueviolet.svg)](https://tailwindcss.com/) [![Chart.js](https://img.shields.io/badge/Chart.js-3.x%2B-red.svg)](https://www.chartjs.org/)

一个基于 Web 的交互式应用，允许用户上传音乐相关的流媒体数据文件（Excel/CSV），进行多种数据分析和可视化操作，并为 Spotify 现场音乐会场景提供决策支持。

## ✨ 主要功能

* **文件上传**: 支持上传 `.xlsx`, `.xls`, `.csv` 格式的数据文件。
* **智能数据字典 (Excel)**:
    * 自动检测 Excel 文件中名为 "Dictionary" 的工作表。
    * 根据字典定义的列类型 (int, float, bool) 筛选可分析列。
    * 无字典或格式不符时，默认使用第一个数据工作表的所有数值型或可转换列。
* **单列数据分析**:
    * **数值型 (Numeric)**: 显示基本统计信息（均值、方差、标准差、最大/最小值、四分位数、计数）和频次分布直方图 (使用 Chart.js)。
    * **布尔型 (Boolean)**: 显示 True/False 的计数和占比饼图 (使用 Chart.js)。
    * **指数加权分析**: 支持选择数值列作为权重，对目标列进行指数加权分析。
* **Top 100 艺术家排行**:
    * 根据 `daily_rank` 进行加权 (`1/rank^2`) 计算得分。
    * 自动处理 `artists` 列中的多个艺术家。
    * 显示 Top 100 艺术家的排名、姓名、最受欢迎曲目（基于最高 `popularity`）、加权平均 `popularity`、加权平均 `loudness` 和总得分。
    * **交叉引用**: 显示该艺术家进入 **Top 100 歌曲榜** 的歌曲及其排名。
    * 支持“加载更多”分页功能。
* **Top 100 歌曲排行**:
    * 根据 `daily_rank` 进行加权 (`1/rank^2`) 计算得分。
    * 优先使用 `spotify_id` 作为唯一标识符，若无则使用 `name`。
    * 显示 Top 100 歌曲的排名、标题、艺术家、专辑、平均 `popularity`、平均 `loudness` 和总得分。
    * **交叉引用**: 显示歌曲的艺术家在 **Top 100 艺人榜** 中的排名。
    * 支持“加载更多”分页功能。
* **导出功能**:
    * 支持将生成的统计图表（直方图、饼图）导出为 PNG 图片（含背景色）。
    * 支持将生成的 Top 100 艺术家或歌曲完整榜单（包含交叉引用信息）导出为 CSV 或 XLSX 文件。
* **Spotify 歌单生成**:
    * 根据 Top 100 歌曲榜单中的 `spotify_id` 生成 Spotify Track URI 列表，方便用户复制创建歌单。
* **用户界面**:
    * 简洁直观的 Web 界面。
    * 支持暗色模式 (Dark Mode) 切换，并记忆用户偏好 (localStorage)。
    * 提供加载状态指示器和用户反馈消息。

## 🛠️ 技术栈

* **后端**:
    * Python 3.9+
    * Flask (Web 框架)
    * Pandas (数据处理与分析)
    * NumPy (数值计算)
    * scikit-learn (用于 MinMaxScaler)
    * openpyxl (用于 XLSX 文件导出)
* **前端**:
    * HTML5
    * Tailwind CSS v3 (通过构建流程生成 CSS)
    * JavaScript (ES6+)
    * Chart.js (数据可视化)
* **开发工具**:
    * Node.js & npm (用于 Tailwind CSS 构建)
    * Python Virtual Environment (推荐)

## 📂 项目结构

.├── data_analyzer_app         # Flask 应用主包

 │   ├── init.py           # 应用工厂 (create_app)

 │   ├── config.py             # 配置文件 (可选)

 │   ├── main                  # 主页/上传蓝图

 │   │   ├── init.py

 │   │   └── routes.py

 │   ├── analysis              # 分析功能蓝图

 │   │   ├── init.py

 │   │   ├── routes.py         # 分析、导出、歌单 API 路由

 │   │   └── utils.py          # 核心数据处理和分析逻辑

 │   │   

 │   ├── static                # 静态文件 (由 Flask 提供服务)

 │   │   ├── dist              # Tailwind 构建输出目录

 │   │   │   └── output.css    # 最终生成的 CSS 文件

 │   │   ├── index.html        # 主 HTML 页面

 │   │   ├── script.js         # 前端 JavaScript 逻辑

 │   │   └── styles.css        # (可能已合并到 input.css)

 │   └── uploads               # 上传文件存储目录 (应用包内)

 ├── src                       # Tailwind 源文件目录

 │   └── input.css             # Tailwind 输入 CSS 文件 (含 @tailwind 指令和自定义样式)

 ├── venv/                     # Python 虚拟环境 (推荐)

 ├── node_modules/             # Node.js 依赖

 ├── cert.pem                  # SSL 证书 (可选, 用于 HTTPS)

 ├── key.pem                   # SSL 私钥 (可选, 用于 HTTPS)

 ├── requirements.txt          # Python 依赖列表

 ├── package.json              # Node.js 项目/依赖配置

 ├── package-lock.json         # Node.js 依赖锁定文件

 ├── tailwind.config.js        # Tailwind CSS 配置文件

 └── run.py                    # Flask 应用启动脚本

 
## 🚀 开始使用

### 先决条件

* Python 3.9 或更高版本
* pip (Python 包管理器)
* Node.js 和 npm (建议使用 LTS 版本)
* Git (用于克隆仓库)

### 安装步骤

1.  **克隆仓库**:
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```

2.  **创建并激活 Python 虚拟环境** (推荐):
    ```bash
    python -m venv venv
    # Windows
    # venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **安装 Python 依赖**:
    ```bash
    pip install -r requirements.txt
    ```
    *(如果 `requirements.txt` 不存在, 您需要先根据导入生成: `pip freeze > requirements.txt`)*

4.  **安装 Node.js 依赖**:
    ```bash
    npm install
    ```

5.  **设置环境变量** (可选, 但推荐):
    * 创建一个 `.env` 文件在项目根目录。
    * 在 `.env` 文件中设置 `SECRET_KEY` (用于 Flask 会话安全，即使现在没用到 session 也建议设置):
        ```
        SECRET_KEY='一个非常复杂且随机的密钥'
        FLASK_APP=run.py
        FLASK_DEBUG=1 # 开发时设为 1, 生产环境设为 0
        ```
    * 您的 `run.py` 或 `config.py` 可能需要加载这些变量 (例如使用 `python-dotenv` 库)。

### 运行应用

您需要**同时运行**两个进程：

1.  **运行 Tailwind CSS 构建 (监视模式)**:
    * 打开**第一个**终端窗口。
    * 进入项目根目录。
    * 运行以下命令 (它会持续监视文件变化并自动重新构建 `output.css`):
        ```bash
        npm run watch:css
        ```
    * 保持这个终端窗口**运行状态**。

2.  **运行 Flask 应用服务器**:
    * 打开**第二个**终端窗口。
    * 确保您的 Python 虚拟环境已激活。
    * 进入项目根目录。
    * 运行 Flask 应用：
        ```bash
        flask run
        ```
        (或者 `python run.py`，取决于您的 `run.py` 如何设置)

3.  **访问应用**:
    * 在浏览器中打开 Flask 服务器运行的地址 (通常是 `http://127.0.0.1:5000` 或 Flask 输出中显示的地址)。

## 📖 使用说明

1.  访问应用主页。
2.  点击“上传文件”按钮，选择符合格式要求的 Excel 或 CSV 文件。
3.  文件上传成功后，左侧会显示可供分析的列。
4.  点击左侧列表中的列名，右侧会显示该列的单列分析结果（统计信息和图表）。
    * 可以选择一个数值型列作为“权重列”进行加权分析。
    * 可以点击图表上方的导出按钮将图表保存为 PNG。
5.  点击“分析 Top 100 艺术家”或“分析 Top 100 歌曲”按钮。
6.  下方会显示对应的 Top 100 排名表格，包含交叉引用信息。
    * 可以点击表格上方的导出按钮将完整榜单保存为 CSV 或 XLSX。
    * 如果是 Top 100 歌曲榜单，还会显示“生成 Spotify 歌单”按钮。点击后会弹出包含 Spotify URI 的文本框供复制。
    * 如果榜单过长，可以点击“加载更多”按钮查看后续排名。
7.  使用右上角的按钮切换亮色/暗色模式。

## 📸 截图

*待添加*

* [截图 1: 主界面]
* [截图 2: 单列分析 (数值型)]
* [截图 3: Top 100 艺术家排行 (含交叉引用)]
* [截图 4: 导出功能]
* [截图 5: Spotify 歌单生成]

## 🔮 未来改进

* **前端 JavaScript 重构**: 将 `script.js` 进一步模块化，分离 API 调用、UI 更新和状态管理逻辑。
* **后端错误处理**: 标准化 JSON 错误响应格式。
* **后端健壮性**: 在 `utils.py` 中添加更严格的数据校验。
* **配置管理**: 使用更完善的配置管理方式（例如 Flask-Env, .env 文件加载）。
* **安全性**: 考虑生产环境中的更多安全措施（文件名安全处理、上传限制等）。
* **测试**: 添加单元测试 (尤其是 `utils.py`) 和集成测试。
* **UI/UX 优化**: 改进加载状态、按钮反馈、图表样式细节、响应式布局等。
* **新功能**:
    * 添加AI支持，解除项目初期为Datathon特定任务而导致的数据耦合需求过高的问题，支持类型更广泛的数据与更灵活的输入输出
    * 支持更多图表类型或分析方法。
    * 支持多列关联分析。
    * 用户账户系统和历史记录。
    * 直接与 Spotify API 集成创建歌单 (需要 OAuth 认证)。
    * 添加成本、收入估算和推广计划模块。

## 🤝 贡献 (可选)

欢迎各种形式的贡献！

## 📄 许可证 (可选)

本项目根据 [MIT 许可证](LICENSE) (如果创建了该文件) 授权。
