# data_analyzer_app/main/routes.py
import os
import logging
import pandas as pd
from flask import request, jsonify, send_from_directory, current_app
from . import main_bp # 从同级 __init__.py 导入蓝图实例

# 导入需要的辅助函数 - 注意相对路径或绝对路径
# 这里假设 analysis_utils 在 analysis 包内
try:
    from ..analysis.utils import get_file_extension, find_first_data_sheet, safe_str_lower, read_datafile
except ImportError:
     # Fallback if structure is slightly different or running script directly
     try:
         from analysis.utils import get_file_extension, find_first_data_sheet, safe_str_lower, read_datafile
     except ImportError:
          # If utils are at the app level instead of analysis level
          try:
              from ..analysis import get_file_extension, find_first_data_sheet, safe_str_lower, read_datafile
          except ImportError:
               logging.error("Could not import utility functions in main/routes.py")
               # Define dummy functions or raise error
               def get_file_extension(f): return ""
               def find_first_data_sheet(s): return None
               def safe_str_lower(v): return str(v).lower()


# 使用蓝图的 logger
logger = logging.getLogger(__name__) # 或者 current_app.logger

@main_bp.route('/')
def serve_index():
    """Serves the main HTML page."""
    # current_app 在请求上下文中可用
    static_folder = current_app.static_folder
    logger.debug(f"Serving index.html from: {static_folder}")
    return send_from_directory(static_folder, 'index.html')

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles file uploads (Excel or CSV). Checks for a 'Dictionary' sheet in Excel files.
    Returns columns allowed for analysis along with their types.
    """
    if 'file' not in request.files:
        logger.warning("No file part in request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if not file or not file.filename:
        logger.warning("No selected file")
        return jsonify({'error': 'No selected file'}), 400

    filename = file.filename # Use secure_filename in production
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    file_ext = get_file_extension(filename)

    allowed_extensions = ['.xlsx', '.xls', '.csv']
    if file_ext not in allowed_extensions:
         logger.warning(f"Upload rejected: Unsupported file type '{file_ext}' for file '{filename}'")
         return jsonify({'error': f'Unsupported file type: {file_ext}. Please upload .xlsx, .xls, or .csv'}), 400

    try:
        # Ensure upload folder exists (also done in create_app, but good practice here too)
        os.makedirs(upload_folder, exist_ok=True)
        file.save(file_path)
        logger.info(f"File saved successfully: {file_path}")
    except Exception as e:
        logger.error(f"Error saving file {filename}: {str(e)}")
        return jsonify({'error': f'File save failed: {str(e)}'}), 500
    # Check after save, before processing
    if not os.path.exists(file_path):
         logger.error(f"File not found after saving: {file_path}")
         return jsonify({'error': 'File save failed (not found after save)'}), 500

    analyzable_columns_with_types = []
    data_sheet_name = None
    try:
        if file_ext in ['.xlsx', '.xls']:
            logger.info(f"Processing Excel file: {filename}")
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            dictionary_sheet_name = None
            for name in sheet_names:
                if name.lower() == 'dictionary': dictionary_sheet_name = name; break
            data_sheet_name = find_first_data_sheet(sheet_names)

            if dictionary_sheet_name:
                logger.info(f"Found 'Dictionary' sheet: {dictionary_sheet_name}")
                try:
                    dict_df = pd.read_excel(excel_file, sheet_name=dictionary_sheet_name)
                    dict_df.columns = [safe_str_lower(col) for col in dict_df.columns]
                    if 'key' in dict_df.columns and 'type' in dict_df.columns:
                        allowed_types = ['int', 'float', 'bool']
                        dict_df['type_norm'] = dict_df['type'].apply(safe_str_lower)
                        filtered_dict = dict_df[dict_df['type_norm'].isin(allowed_types)].copy()
                        potential_columns = filtered_dict[['key', 'type_norm']].to_dict('records')
                        potential_columns = [{'name': item['key'], 'type': item['type_norm']} for item in potential_columns if item.get('key')]
                        if data_sheet_name:
                            # Read only necessary columns if possible, or just check existence
                            data_df_cols = pd.read_excel(excel_file, sheet_name=data_sheet_name, nrows=0).columns # Read only header
                            data_columns_set = set(data_df_cols)
                            analyzable_columns_with_types = [col_info for col_info in potential_columns if col_info['name'] in data_columns_set]
                        else: analyzable_columns_with_types = []
                    else: # Fallback
                         logger.warning("'Dictionary' sheet format invalid. Falling back.")
                         if data_sheet_name: data_df = pd.read_excel(excel_file, sheet_name=data_sheet_name, nrows=0); analyzable_columns_with_types = [{'name': col, 'type': 'numeric'} for col in data_df.columns]
                         else: raise ValueError("No data sheets found.")
                except Exception as dict_read_e: # Fallback
                    logger.error(f"Error reading 'Dictionary': {dict_read_e}. Falling back.")
                    if data_sheet_name: data_df = pd.read_excel(excel_file, sheet_name=data_sheet_name, nrows=0); analyzable_columns_with_types = [{'name': col, 'type': 'numeric'} for col in data_df.columns]
                    else: raise ValueError("No data sheets found.")
            else: # Fallback
                logger.info("'Dictionary' sheet not found. Using first data sheet.")
                if data_sheet_name: data_df = pd.read_excel(excel_file, sheet_name=data_sheet_name, nrows=0); analyzable_columns_with_types = [{'name': col, 'type': 'numeric'} for col in data_df.columns]
                else: raise ValueError("No data sheets found.")
        elif file_ext == '.csv':
            logger.info(f"Processing CSV file: {filename}")
            # Read only header to get columns quickly
            try:
                 df_cols = pd.read_csv(file_path, encoding='utf-8-sig', nrows=0).columns
            except UnicodeDecodeError:
                 df_cols = pd.read_csv(file_path, encoding='latin1', nrows=0).columns
            analyzable_columns_with_types = [{'name': col, 'type': 'numeric'} for col in df_cols]

        # Final checks
        if not analyzable_columns_with_types and file_ext in ['.xlsx', '.xls'] and data_sheet_name is None: raise ValueError('Could not find analyzable data in the Excel file.')
        if not analyzable_columns_with_types and data_sheet_name is not None: logger.warning(f"No columns were determined analyzable for data source '{data_sheet_name}'.")

        return jsonify({'filename': filename, 'columns': analyzable_columns_with_types})
    except ValueError as e:
         logger.error(f"Value error processing file {filename}: {e}")
         return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Error processing file {filename}: {e}")
        return jsonify({'error': f'Failed to process file content: {str(e)}'}), 500

