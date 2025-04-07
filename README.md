# DATA-THONE: Music Data Analysis and Visualization Platform

[English](README.md) | [简体中文](README.zh.md)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/) [![Flask](https://img.shields.io/badge/Flask-2.x%2B-green.svg)](https://flask.palletsprojects.com/) [![Pandas](https://img.shields.io/badge/Pandas-1.x%2B-yellow.svg)](https://pandas.pydata.org/) [![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-blueviolet.svg)](https://tailwindcss.com/) [![Chart.js](https://img.shields.io/badge/Chart.js-3.x%2B-red.svg)](https://www.chartjs.org/)

An interactive web-based application that allows users to upload music-related streaming data files (Excel/CSV), perform various data analysis and visualization operations, and provide decision support for Spotify live concert scenarios.

## ✨ Main Features

* **File Upload**: Supports uploading `.xlsx`, `.xls`, `.csv` format data files.
* **Intelligent Data Dictionary (Excel)**:
    * Automatically detects a worksheet named "Dictionary" in Excel files.
    * Filters analyzable columns based on column types (int, float, bool) defined in the dictionary.
    * If no dictionary exists or the format is incorrect, defaults to using all numeric or convertible columns from the first data worksheet.
* **Single Column Data Analysis**:
    * **Numeric**: Displays basic statistics (mean, variance, standard deviation, max/min, quartiles, count) and a frequency distribution histogram (using Chart.js).
    * **Boolean**: Displays counts and a percentage pie chart for True/False values (using Chart.js).
    * **Exponential Weighted Analysis**: Supports selecting a numeric column as weights for exponential weighted analysis on the target column.
* **Top 100 Artists Ranking**:
    * Calculates scores based on `daily_rank` weighting (`1/rank^2`).
    * Automatically handles multiple artists in the `artists` column.
    * Displays the Top 100 artists' rank, name, most popular track (based on highest `popularity`), weighted average `popularity`, weighted average `loudness`, and total score.
    * **Cross-reference**: Shows the artist's songs that entered the **Top 100 Songs Chart** and their ranks.
    * Supports "Load More" pagination.
* **Top 100 Songs Ranking**:
    * Calculates scores based on `daily_rank` weighting (`1/rank^2`).
    * Uses `spotify_id` as the unique identifier primarily; falls back to `name` if unavailable.
    * Displays the Top 100 songs' rank, title, artist, album, average `popularity`, average `loudness`, and total score.
    * **Cross-reference**: Shows the rank of the song's artist in the **Top 100 Artists Chart**.
    * Supports "Load More" pagination.
* **Export Functionality**:
    * Supports exporting generated statistical charts (histograms, pie charts) as PNG images (with background color).
    * Supports exporting the complete Top 100 Artists or Songs lists (including cross-referenced information) as CSV or XLSX files.
* **Spotify Playlist Generation**:
    * Generates a list of Spotify Track URIs based on the `spotify_id` from the Top 100 Songs list, making it easy for users to copy and create playlists.
* **User Interface**:
    * Clean and intuitive web interface.
    * Supports Dark Mode toggle with user preference saved (localStorage).
    * Provides loading status indicators and user feedback messages.

## 🛠️ Technology Stack

* **Backend**:
    * Python 3.9+
    * Flask (Web Framework)
    * Pandas (Data Processing and Analysis)
    * NumPy (Numerical Computation)
    * scikit-learn (for MinMaxScaler)
    * openpyxl (for XLSX file export)
* **Frontend**:
    * HTML5
    * Tailwind CSS v3 (CSS generated via build process)
    * JavaScript (ES6+)
    * Chart.js (Data Visualization)
* **Development Tools**:
    * Node.js & npm (for Tailwind CSS build)
    * Python Virtual Environment (Recommended)

## 📂 Project Structure

.
├── data_analyzer_app         # Main Flask application package  
│   ├── init.py           # Application factory (create_app)  
│   ├── config.py             # Configuration file (optional)  
│   ├── main                  # Main page/upload blueprint  
│   │   ├── init.py  
│   │   └── routes.py  
│   ├── analysis              # Analysis features blueprint  
│   │   ├── init.py  
│   │   ├── routes.py         # Analysis, export, playlist API routes  
│   │   └── utils.py          # Core data processing and analysis logic  
│   │  
│   ├── static                # Static files (served by Flask)  
│   │   ├── dist              # Tailwind build output directory  
│   │   │   └── output.css    # Final generated CSS file  
│   │   ├── index.html        # Main HTML page  
│   │   ├── script.js         # Frontend JavaScript logic  
│   │   └── styles.css        # (Potentially merged into input.css)  
│   └── uploads               # Uploaded file storage directory (within app package)  
├── src                       # Tailwind source files directory  
│   └── input.css             # Tailwind input CSS file (with @tailwind directives and custom styles)  
├── venv/                     # Python virtual environment (Recommended)  
├── node_modules/             # Node.js dependencies  
├── cert.pem                  # SSL certificate (optional, for HTTPS)  
├── key.pem                   # SSL private key (optional, for HTTPS)  
├── requirements.txt          # Python dependency list  
├── package.json              # Node.js project/dependency configuration  
├── package-lock.json         # Node.js dependency lock file  
├── tailwind.config.js        # Tailwind CSS configuration file  
└── run.py                    # Flask application startup script  


## 🚀 Getting Started

### Prerequisites

* Python 3.9 or later
* pip (Python package manager)
* Node.js and npm (LTS version recommended)
* Git (for cloning the repository)

### Installation Steps

1.  **Clone the repository**:
    ```bash
    git clone <your-repository-url>
    cd <repository-folder>
    ```

2.  **Create and activate a Python virtual environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows
    # venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` does not exist, you may need to generate it first based on your imports: `pip freeze > requirements.txt`)*

4.  **Install Node.js dependencies**:
    ```bash
    npm install
    ```

5.  **Set environment variables** (Optional, but recommended):
    * Create a `.env` file in the project root directory.
    * Set `SECRET_KEY` in the `.env` file (for Flask session security, recommended even if sessions aren't currently used):
        ```
        SECRET_KEY='a_very_complex_and_random_secret_key'
        FLASK_APP=run.py
        FLASK_DEBUG=1 # Set to 1 for development, 0 for production
        ```
    * Your `run.py` or `config.py` might need to load these variables (e.g., using the `python-dotenv` library).

### Running the Application

You need to run **two processes concurrently**:

1.  **Run the Tailwind CSS build (watch mode)**:
    * Open your **first** terminal window.
    * Navigate to the project root directory.
    * Run the following command (it will continuously watch for file changes and rebuild `output.css` automatically):
        ```bash
        npm run watch:css
        ```
    * Keep this terminal window **running**.

2.  **Run the Flask application server**:
    * Open a **second** terminal window.
    * Ensure your Python virtual environment is activated.
    * Navigate to the project root directory.
    * Run the Flask application:
        ```bash
        flask run
        ```
        (Or `python run.py`, depending on how your `run.py` is set up)

3.  **Access the application**:
    * Open the address where the Flask server is running in your browser (usually `http://127.0.0.1:5000` or the address shown in the Flask output).

## 📖 Usage Instructions

1.  Visit the application's main page.
2.  Click the "Upload File" button and select an Excel or CSV file meeting the format requirements.
3.  After successful upload, the analyzable columns will be displayed on the left.
4.  Click a column name in the left list to view its single-column analysis results (statistics and chart) on the right.
    * You can select a numeric column as the "Weight Column" for weighted analysis.
    * You can click the export button above the chart to save it as a PNG.
5.  Click the "Analyze Top 100 Artists" or "Analyze Top 100 Songs" button.
6.  The corresponding Top 100 ranking table will be displayed below, including cross-referenced information.
    * You can click the export button above the table to save the complete list as CSV or XLSX.
    * For the Top 100 Songs list, a "Generate Spotify Playlist" button will also appear. Clicking it reveals a text box with Spotify URIs for copying.
    * If the list is long, click the "Load More" button to view subsequent rankings.
7.  Use the button in the top-right corner to toggle between Light/Dark mode.

## 📸 Screenshots

*To be added*

* [Screenshot 1: Main Interface]
* [Screenshot 2: Single Column Analysis (Numeric)]
* [Screenshot 3: Top 100 Artists Ranking (with Cross-reference)]
* [Screenshot 4: Export Functionality]
* [Screenshot 5: Spotify Playlist Generation]

## 🔮 Future Improvements

* **Frontend JavaScript Refactoring**: Further modularize `script.js`, separating API calls, UI updates, and state management logic.
* **Backend Error Handling**: Standardize JSON error response formats.
* **Backend Robustness**: Add stricter data validation in `utils.py`.
* **Configuration Management**: Implement a more robust configuration management approach (e.g., Flask-Env, loading .env files).
* **Security**: Consider more security measures for production environments (secure filename handling, upload limits, etc.).
* **Testing**: Add unit tests (especially for `utils.py`) and integration tests.
* **UI/UX Optimization**: Improve loading states, button feedback, chart styling details, responsive layout, etc.
* **New Features**:
    * Add AI support to overcome the high data coupling requirements from the initial Datathon-specific tasks, supporting a wider range of data types and more flexible inputs/outputs.
    * Support more chart types or analysis methods.
    * Support multi-column correlation analysis.
    * User account system and history tracking.
    * Direct integration with Spotify API to create playlists (requires OAuth authentication).
    * Add modules for cost/revenue estimation and promotion planning.

## 🤝 Contributing (Optional)

Contributions of all kinds are welcome!

## 📄 License (Optional)

This project is licensed under the [MIT License](LICENSE) (if you created the file).
