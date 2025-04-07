# data_analyzer_app/analysis/routes.py

# 确保文件顶部有以下或类似的导入语句:
import os
import logging
import pandas as pd
import numpy as np
import io
from flask import (
    Blueprint, request, jsonify, current_app,
    send_file, make_response
)
from sklearn.preprocessing import MinMaxScaler
# 使用相对导入从同级 utils.py 导入
from .utils import (
    read_datafile,
    get_file_extension,
    detect_and_process_boolean,
    calculate_numeric_stats_histogram,
    calculate_artist_metrics,
    get_ranked_artists_df,
    get_ranked_songs_df # 确保这个函数返回包含 spotify_id 的 DataFrame
)

logger = logging.getLogger(__name__)

# 从同级 __init__.py 导入蓝图实例
from . import analysis_bp

@analysis_bp.route('/data', methods=['GET'])
def get_data():
    """
    Handles single column analysis request. Reads data, applies optional weighting,
    detects type, and returns results using helper functions from utils.py.
    """
    # (Code for this route remains the same as before)
    # ...
    filename = request.args.get('file'); col_name = request.args.get('col'); weight_col = request.args.get('weight_col')
    if not filename or not col_name: return jsonify({'error': 'Missing file or column parameter'}), 400
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename); file_ext = get_file_extension(filename)
    if not os.path.exists(file_path): return jsonify({'error': 'File not found on server. Please upload again.'}), 404
    data_sheet_name = None
    try:
        df, source_name = read_datafile(file_path, file_ext); data_sheet_name = source_name
        if col_name not in df.columns: return jsonify({'error': f'Target Column "{col_name}" not found in the data source "{source_name}"'}), 404
        norm_weights = None; weighted_by = None; target_series = df[col_name]
        if weight_col:
            if weight_col not in df.columns: return jsonify({'error': f'Weighting column "{weight_col}" not found.'}), 400
            weight_series = df[weight_col]; temp_df = pd.DataFrame({'target': target_series, 'weight': weight_series}).dropna()
            if temp_df.empty: return jsonify({'type': 'empty', 'message': 'No non-NaN data available for weighting.'}), 200
            if not pd.api.types.is_numeric_dtype(temp_df['weight']): return jsonify({'error': f'Weighting column "{weight_col}" must be numeric.'}), 400
            try:
                scaler = MinMaxScaler(); weights_reshaped = temp_df['weight'].values.reshape(-1, 1); scaled_weights = scaler.fit_transform(weights_reshaped).flatten()
                exp_weights = np.exp(scaled_weights); sum_exp_weights = np.sum(exp_weights)
                if sum_exp_weights > 1e-9 and np.isfinite(sum_exp_weights): norm_weights = exp_weights / sum_exp_weights
                else: norm_weights = np.ones(len(temp_df)) / len(temp_df)
                target_series = temp_df['target']; weighted_by = weight_col
            except Exception as weight_calc_e: return jsonify({'error': f'Failed to calculate weights using column "{weight_col}".'}), 500
        else: target_series = target_series.dropna()
        if target_series.empty: return jsonify({'type': 'empty', 'message': f'Column "{col_name}" contains no analyzable data.'}), 200
        is_boolean, bool_counts = detect_and_process_boolean(target_series, norm_weights)
        if is_boolean: return jsonify({ 'type': 'boolean', 'counts': bool_counts, 'weighted_by': weighted_by })
        else:
            try:
                numeric_col_data = pd.to_numeric(target_series, errors='coerce'); valid_data = numeric_col_data.dropna(); final_weights = None
                if norm_weights is not None:
                     original_indices_of_valid = target_series.index[numeric_col_data.notna()]
                     try:
                         weight_mask = target_series.index.isin(original_indices_of_valid)
                         if len(weight_mask) == len(norm_weights):
                             aligned_weights = norm_weights[weight_mask]
                             sum_aligned_weights = np.sum(aligned_weights)
                             if sum_aligned_weights > 1e-9 and np.isfinite(sum_aligned_weights): final_weights = aligned_weights / sum_aligned_weights
                             else: final_weights = np.ones(len(valid_data)) / len(valid_data) if len(valid_data) > 0 else None
                         else: final_weights = np.ones(len(valid_data)) / len(valid_data) if len(valid_data) > 0 else None
                     except Exception as align_e: final_weights = np.ones(len(valid_data)) / len(valid_data) if len(valid_data) > 0 else None
                else: final_weights = None
                if valid_data.empty: return jsonify({'type': 'empty', 'message': f'Column "{col_name}" contains no valid numeric data after processing.'}), 200
                stats, histogram_data = calculate_numeric_stats_histogram(valid_data, final_weights)
                if not stats and not histogram_data: return jsonify({'error': f'Calculation failed for numeric column "{col_name}". Check server logs.'}), 500
                return jsonify({ 'type': 'numeric', 'stats': stats, 'histogram': histogram_data, 'weighted_by': weighted_by })
            except Exception as numeric_processing_e: return jsonify({'error': f'Failed to process numeric data for column "{col_name}".'}), 500
    except FileNotFoundError: return jsonify({'error': 'File not found on server. Please upload again.'}), 404
    except KeyError as e: source_name = data_sheet_name if data_sheet_name else filename; return jsonify({'error': f'Column "{e}" not found in data source "{source_name}"'}), 404
    except ValueError as e: return jsonify({'error': str(e)}), 400
    except Exception as e: logger.exception(f"Error processing /data request for {filename}, column {col_name}: {str(e)}"); return jsonify({'error': f'Failed to process data request: {str(e)}'}), 500


# ***** 重要：暂时将日志级别设为 DEBUG 以查看详细输出 *****
logger.setLevel(logging.DEBUG)
# *******************************************************

# --- /top_artists 路由 (添加详细日志) ---
@analysis_bp.route('/top_artists', methods=['GET'])
def get_top_artists():
    """
    Analyzes data to find top artists based on daily rank weighting.
    Adds info about artist's songs in the Top 100 Songs list, replacing 'top_track'.
    Supports pagination. Returns ranked list slice and total count.
    Handles NaN conversion to null for JSON compatibility.
    Corrects song lookup logic ensuring consistent ID usage.
    """
    filename = request.args.get('file')
    try:
        page = int(request.args.get('page', 1)); page_size = int(request.args.get('page_size', 10))
        if page < 1: page = 1
        if page_size < 1: page_size = 10
        if page_size > 100: page_size = 100
    except ValueError: return jsonify({'error': 'Invalid page or page_size parameter.'}), 400

    if not filename: return jsonify({'error': 'Missing file parameter'}), 400
    upload_folder = current_app.config['UPLOAD_FOLDER']; file_path = os.path.join(upload_folder, filename)
    file_ext = get_file_extension(filename)
    if not os.path.exists(file_path): return jsonify({'error': 'File not found on server. Please upload again.'}), 404

    try:
        df, source_name = read_datafile(file_path, file_ext)

        # --- 1. Get FULL Ranked Lists ---
        ranked_artists_df = get_ranked_artists_df(df)
        ranked_songs_df = get_ranked_songs_df(df) # Should now reliably contain 'Spotify ID' or 'Name'

        if ranked_artists_df.empty: return jsonify({'error': 'Could not generate artist ranking.'}), 400
        if ranked_songs_df.empty: logger.warning("Could not generate song ranking for cross-referencing."); ranked_songs_df = pd.DataFrame(columns=['Rank', 'Name', 'Spotify ID'])

        # --- 2. Create Top 100 Songs Lookup (Prioritize Spotify ID) ---
        # ***** 修正点: 确定 lookup 使用的列名 *****
        if 'Spotify ID' in ranked_songs_df.columns:
            song_id_col_lookup = 'Spotify ID'
            logger.info("Using 'Spotify ID' for song lookup dictionary.")
        elif 'Name' in ranked_songs_df.columns:
            song_id_col_lookup = 'Name'
            logger.warning("Using 'Name' for song lookup dictionary (Spotify ID missing in ranked songs).")
        else:
            logger.error("Cannot create song lookup: Missing 'Spotify ID' and 'Name' in ranked songs.")
            top_100_songs_lookup = {} # Create empty lookup

        # 创建查找表，确保 key 是干净的字符串，如果是 Name 则小写
        top_100_songs_lookup = {}
        if song_id_col_lookup: # Proceed only if a lookup column was determined
            for index, row in ranked_songs_df.head(100).iterrows():
                key = row[song_id_col_lookup]
                if pd.notna(key):
                    clean_key = str(key).strip()
                    if song_id_col_lookup == 'Name': clean_key = clean_key.lower()
                    if clean_key: top_100_songs_lookup[clean_key] = row['Rank']
            logger.debug(f"Top 100 songs lookup created using '{song_id_col_lookup}' with {len(top_100_songs_lookup)} entries.")
            # logger.debug(f"Sample lookup keys: {list(top_100_songs_lookup.keys())[:10]}")

        # --- 3. Augment Artist Data ---
        # ***** 修正点: 确定原始数据中使用的 ID 列，与 lookup 保持一致 *****
        if 'spotify_id' in df.columns and song_id_col_lookup == 'Spotify ID':
             orig_song_id_col = 'spotify_id'
             id_is_name = False
             logger.info("Using 'spotify_id' from original data for artist song matching.")
        elif 'name' in df.columns: # Fallback to name if spotify_id not present OR if lookup uses Name
             orig_song_id_col = 'name'
             id_is_name = True
             logger.info("Using 'name' from original data for artist song matching.")
        else:
             logger.error("Cannot find artist songs: Missing 'spotify_id'/'name' in original data.")
             orig_song_id_col = None # Flag that we cannot proceed

        if orig_song_id_col and 'artists' in df.columns and 'name' in df.columns:
             df_orig_songs = df[['artists', orig_song_id_col, 'name']].copy()
             df_orig_songs['artists'] = df_orig_songs['artists'].astype(str).fillna('')
             df_orig_songs['artists_list'] = df_orig_songs['artists'].str.split(r'\s*,\s*')
             # 清理原始数据的 ID 列
             df_orig_songs[orig_song_id_col] = df_orig_songs[orig_song_id_col].astype(str).str.strip()
             if id_is_name: df_orig_songs[orig_song_id_col] = df_orig_songs[orig_song_id_col].str.lower()

             # 歌曲名称查找表 (key 是清理过的 ID)
             song_name_map = df_orig_songs.dropna(subset=[orig_song_id_col]).set_index(orig_song_id_col)['name'].to_dict()

             def find_artist_top_songs(artist_name):
                 artist_songs_info = []; clean_artist_name_lower = artist_name.strip().lower()
                 logger.debug(f"--- Processing artist: '{artist_name}' ---")
                 try:
                     mask = df_orig_songs['artists_list'].apply(lambda artists: isinstance(artists, list) and clean_artist_name_lower in [a.strip().lower() for a in artists])
                     artist_song_ids = df_orig_songs.loc[mask, orig_song_id_col].unique()
                     logger.debug(f"Found {len(artist_song_ids)} unique song IDs ({orig_song_id_col}) for '{artist_name}'.")

                     found_count = 0
                     for song_id in artist_song_ids:
                         if not song_id: continue
                         lookup_key = song_id # ID 已经是处理过的
                         logger.debug(f"  Checking lookup_key: '{lookup_key}' (Type: {type(lookup_key)}) against lookup using '{song_id_col_lookup}'")

                         if lookup_key in top_100_songs_lookup: # Use the cleaned ID for lookup
                             found_count += 1
                             song_rank = top_100_songs_lookup[lookup_key]
                             song_name = song_name_map.get(lookup_key, 'Unknown Name')
                             artist_songs_info.append(f"{song_name} (Rank: {song_rank})")
                             logger.debug(f"  -> SUCCESS! Rank: {song_rank}, Name: {song_name}")
                         # else: # Keep logs cleaner unless needed
                         #     logger.debug(f"  -> FAILED! Key '{lookup_key}' not found.")
                 except Exception as e: logger.error(f"Error finding top songs for artist {artist_name}: {e}", exc_info=True); return "Error finding songs"
                 logger.debug(f"Finished '{artist_name}'. Found {found_count} songs in Top 100 lookup.")
                 return "<br>".join(artist_songs_info) if artist_songs_info else "-"

             logger.info("Augmenting artist data with Top 100 song info...")
             ranked_artists_df['top_songs_info'] = ranked_artists_df['Artist'].apply(find_artist_top_songs)
             logger.info("Finished augmenting artist data.")
        else:
             logger.warning("Skipping artist song cross-reference due to missing columns.")
             ranked_artists_df['top_songs_info'] = '-' # Ensure column exists

        # --- 4. Paginate ---
        total_artists = len(ranked_artists_df); start_index = (page - 1) * page_size; end_index = start_index + page_size
        paginated_results = ranked_artists_df[start_index:end_index]
        if paginated_results.empty and page > 1: return jsonify({'artists': [], 'total_artists': total_artists})

        # --- 5. Format Output ---
        paginated_results_no_nan = paginated_results.replace({np.nan: None})
        final_output_list = []
        for _, row in paginated_results_no_nan.iterrows():
             artist_data = {
                 'rank': row['Rank'], 'artist': row['Artist'],
                 'top_songs_info': row['top_songs_info'], # Unified column
                 'avg_popularity': row['Avg Popularity'], 'avg_loudness': row['Avg Loudness'],
                 'score': row['Score'], 'unique_songs': row.get('Unique Songs', None),
                 'total_entries': row.get('Total Entries', None),
             }
             final_output_list.append(artist_data)
        logger.info(f"Returning page {page} ({len(final_output_list)} artists) of {total_artists} total ranked artists with unified cross-ref info.")
        return jsonify({'artists': final_output_list, 'total_artists': total_artists})

    # --- Error Handling ---
    except FileNotFoundError: return jsonify({'error': 'File not found on server. Please upload again.'}), 404
    except KeyError as e: return jsonify({'error': f'Required column "{e}" not found in data source for artist analysis.'}), 400
    except ValueError as e: return jsonify({'error': str(e)}), 400
    except Exception as e: logger.exception(f"Unexpected error during artist analysis for {filename}: {str(e)}"); return jsonify({'error': f'Failed to perform artist analysis: {str(e)}'}), 500

# --- /top_songs 路由 (包含交叉引用逻辑) ---
@analysis_bp.route('/top_songs', methods=['GET'])
def get_top_songs():
    """
    Analyzes data to find top songs based on daily rank weighting.
    Adds info about song's artists in the Top 100 Artists list.
    Supports pagination. Returns ranked list slice and total count.
    Handles NaN conversion to null for JSON compatibility.
    """
    filename = request.args.get('file')
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        if page < 1: page = 1
        if page_size < 1: page_size = 10
        if page_size > 100: page_size = 100
    except ValueError:
        return jsonify({'error': 'Invalid page or page_size parameter. Must be integers.'}), 400

    if not filename: return jsonify({'error': 'Missing file parameter'}), 400

    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    file_ext = get_file_extension(filename)
    if not os.path.exists(file_path): return jsonify({'error': 'File not found on server. Please upload again.'}), 404

    try:
        df, source_name = read_datafile(file_path, file_ext)

        # --- 1. Get FULL Ranked Lists ---
        ranked_songs_df = get_ranked_songs_df(df)
        ranked_artists_df = get_ranked_artists_df(df) # Need this for lookup

        if ranked_songs_df.empty:
             return jsonify({'error': 'Could not generate song ranking.'}), 400
        if ranked_artists_df.empty:
             logger.warning("Could not generate artist ranking for cross-referencing, proceeding without it.")
             ranked_artists_df = pd.DataFrame(columns=['Rank', 'Artist'])

        # --- 2. Create Top 100 Artists Lookup ---
        top_100_artists_lookup = {
            # 键是 Artist 列的值 (来自 get_ranked_artists_df 的输出)
            row['Artist']: row['Rank']
            for index, row in ranked_artists_df.head(100).iterrows()
            if pd.notna(row['Artist'])
        }
        logger.debug(f"Top 100 artists lookup created with {len(top_100_artists_lookup)} entries.")

        # --- 3. Augment Song Data ---
        # 需要 'Artists' 字符串列 (来自 get_ranked_songs_df 的输出)
        if 'Artists' not in ranked_songs_df.columns:
             logger.warning("Ranked songs DataFrame missing 'Artists' column. Skipping cross-reference.")
             # 如果缺少 'Artists' 列，则创建一个默认值列
             ranked_songs_df['artist_ranks_info'] = ranked_songs_df.get('Artists', pd.Series(['-'] * len(ranked_songs_df))).fillna('-')
        else:
            def find_song_artist_ranks(artists_string):
                if not artists_string or pd.isna(artists_string):
                    return "-"
                # 假设原始 'Artists' 列是逗号分隔
                artists = [a.strip() for a in str(artists_string).split(r',')]
                ranks_info = []
                for artist in artists:
                    if not artist: continue # 跳过空艺术家名
                    # 使用 .get() 进行查找，如果找不到则返回 '-'
                    rank = top_100_artists_lookup.get(artist.strip(), '-') # 确保查找时也去除空格
                    ranks_info.append(f"{artist.strip()} (Rank: {rank})")
                # 使用 <br> 连接，以便在 HTML 中换行显示
                return "<br>".join(ranks_info) if ranks_info else "-"

            logger.info("Augmenting song data with Top 100 artist rank info...")
            ranked_songs_df['artist_ranks_info'] = ranked_songs_df['Artists'].apply(find_song_artist_ranks)
            logger.info("Finished augmenting song data.")

        # --- 4. Paginate Augmented Results ---
        total_songs = len(ranked_songs_df)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_results = ranked_songs_df[start_index:end_index]

        if paginated_results.empty and page > 1:
             return jsonify({'songs': [], 'total_songs': total_songs})

        # --- 5. Format Output (Handle NaN before creating list) ---
        paginated_results_no_nan = paginated_results.replace({np.nan: None})

        final_output_list = []
        # 确定 Spotify ID 列名 (可能由 get_ranked_songs_df 重命名)
        song_id_col_name = 'Spotify ID' if 'Spotify ID' in paginated_results_no_nan.columns else None

        for _, row in paginated_results_no_nan.iterrows():
             song_data = {
                 'rank': row['Rank'],
                 'name': row['Name'],
                 'artists': row['Artists'], # 原始艺术家字符串
                 'album': row['Album'],
                 'popularity': row['Popularity'],
                 'loudness': row['Loudness'],
                 'score': row['Score'],
                 'artist_ranks_info': row['artist_ranks_info'] # 新增字段
             }
             if song_id_col_name:
                 song_data['spotify_id'] = row[song_id_col_name] # 如果存在，添加 spotify_id
             final_output_list.append(song_data)

        logger.info(f"Returning page {page} ({len(final_output_list)} songs) of {total_songs} total ranked songs with cross-ref info.")
        return jsonify({'songs': final_output_list, 'total_songs': total_songs})

    # --- Error Handling ---
    except FileNotFoundError: return jsonify({'error': 'File not found on server. Please upload again.'}), 404
    except KeyError as e: return jsonify({'error': f'Required column "{e}" not found in data source for song analysis.'}), 400
    except ValueError as e: return jsonify({'error': str(e)}), 400
    except Exception as e: logger.exception(f"Unexpected error during song analysis for {filename}: {str(e)}"); return jsonify({'error': f'Failed to perform song analysis: {str(e)}'}), 500

# --- 修改 /export/ranking 路由 ---
@analysis_bp.route('/export/ranking', methods=['GET'])
def export_ranking():
    """
    Exports the full ranked list (artists or songs) as a CSV or XLSX file,
    INCLUDING cross-referenced Top 100 information.
    Query Parameters:
        file (str): The name of the uploaded data file. Required.
        type (str): 'artists' or 'songs'. Required.
        format (str): 'csv' or 'xlsx'. Optional, defaults to 'csv'.
    """
    filename = request.args.get('file')
    export_type = request.args.get('type')
    export_format = request.args.get('format', 'csv').lower()

    if not filename: return jsonify({'error': 'Missing required parameter: file'}), 400
    if not export_type or export_type not in ['artists', 'songs']: return jsonify({'error': "Missing or invalid required parameter: type (must be 'artists' or 'songs')"}), 400
    if export_format not in ['csv', 'xlsx']: return jsonify({'error': "Invalid parameter: format (must be 'csv' or 'xlsx')"}), 400

    upload_folder = current_app.config['UPLOAD_FOLDER']; file_path = os.path.join(upload_folder, filename)
    file_ext = get_file_extension(filename)
    if not os.path.exists(file_path): return jsonify({'error': 'File not found on server. Please upload again.'}), 404

    try:
        df, source_name = read_datafile(file_path, file_ext)

        # --- 1. Get FULL Ranked Lists (Needed for both cases for cross-ref) ---
        ranked_artists_full = get_ranked_artists_df(df)
        ranked_songs_full = get_ranked_songs_df(df)

        # Initialize empty df for safety
        ranked_df_augmented = pd.DataFrame()

        # --- 2. Augment Data Based on Export Type ---
        if export_type == 'artists':
            ranked_df = ranked_artists_full # Start with base artist ranking
            if ranked_df.empty: return jsonify({'error': 'Could not generate artist ranking for export.'}), 400

            # --- Create Top 100 Songs Lookup ---
            if ranked_songs_full.empty: logger.warning("Cannot add song cross-reference to artist export: Song ranking failed."); ranked_df['Top 100 Songs (Rank)'] = '-'
            else:
                song_id_col_lookup = 'Spotify ID' if 'Spotify ID' in ranked_songs_full.columns else 'Name'
                top_100_songs_lookup = {}
                for index, row in ranked_songs_full.head(100).iterrows():
                    key = row[song_id_col_lookup]; rank = row['Rank']
                    if pd.notna(key):
                        clean_key = str(key).strip()
                        if song_id_col_lookup == 'Name': clean_key = clean_key.lower()
                        if clean_key: top_100_songs_lookup[clean_key] = rank
                logger.debug(f"[Export] Top 100 songs lookup created using '{song_id_col_lookup}' with {len(top_100_songs_lookup)} entries.")

                # --- Define Function to Find Artist's Top Songs (for export) ---
                orig_song_id_col = 'spotify_id' if 'spotify_id' in df.columns and song_id_col_lookup == 'Spotify ID' else 'name'
                id_is_name = (orig_song_id_col == 'name')
                song_name_map = {}
                if orig_song_id_col in df.columns and 'artists' in df.columns and 'name' in df.columns:
                    df_orig_songs = df[['artists', orig_song_id_col, 'name']].copy()
                    df_orig_songs['artists'] = df_orig_songs['artists'].astype(str).fillna('')
                    df_orig_songs['artists_list'] = df_orig_songs['artists'].str.split(r'\s*,\s*')
                    df_orig_songs[orig_song_id_col] = df_orig_songs[orig_song_id_col].astype(str).str.strip()
                    if id_is_name: df_orig_songs[orig_song_id_col] = df_orig_songs[orig_song_id_col].str.lower()
                    song_name_map = df_orig_songs.dropna(subset=[orig_song_id_col]).set_index(orig_song_id_col)['name'].to_dict()

                    def find_artist_top_songs_export(artist_name):
                        artist_songs_info = []; clean_artist_name_lower = artist_name.strip().lower()
                        try:
                            mask = df_orig_songs['artists_list'].apply(lambda artists: isinstance(artists, list) and clean_artist_name_lower in [a.strip().lower() for a in artists])
                            artist_song_ids = df_orig_songs.loc[mask, orig_song_id_col].unique()
                            for song_id in artist_song_ids:
                                if not song_id: continue
                                lookup_key = song_id
                                if lookup_key in top_100_songs_lookup:
                                    song_rank = top_100_songs_lookup[lookup_key]
                                    song_name = song_name_map.get(lookup_key, 'Unknown Name')
                                    artist_songs_info.append(f"{song_name} (Rank: {song_rank})")
                        except Exception as e: logger.error(f"[Export] Error finding top songs for {artist_name}: {e}"); return "Error"
                        # ***** 修改点: 使用 ', ' 作为分隔符 *****
                        return ", ".join(artist_songs_info) if artist_songs_info else "-"
                        # ***************************************
                else:
                     find_artist_top_songs_export = lambda artist_name: '-' # Fallback if needed cols missing

                # --- Apply Function to Add Column ---
                ranked_df['Top 100 Songs (Rank)'] = ranked_df['Artist'].apply(find_artist_top_songs_export)

            ranked_df_augmented = ranked_df # Assign augmented df

        elif export_type == 'songs':
            ranked_df = ranked_songs_full # Start with base song ranking
            if ranked_df.empty: return jsonify({'error': 'Could not generate song ranking for export.'}), 400

            # --- Create Top 100 Artists Lookup ---
            if ranked_artists_full.empty: logger.warning("Cannot add artist cross-reference to song export: Artist ranking failed."); ranked_df['Artist(s) (Top 100 Rank)'] = ranked_df.get('Artists', '-')
            else:
                top_100_artists_lookup = {}
                for index, row in ranked_artists_full.head(100).iterrows():
                    key = row['Artist']
                    if pd.notna(key):
                        clean_key = str(key).strip()
                        if clean_key: top_100_artists_lookup[clean_key] = row['Rank']
                logger.debug(f"[Export] Top 100 artists lookup created with {len(top_100_artists_lookup)} entries.")

                # --- Define Function to Find Song's Artist Ranks (for export) ---
                def find_song_artist_ranks_export(artists_string):
                    if not artists_string or pd.isna(artists_string): return "-"
                    artists = [a.strip() for a in str(artists_string).split(r',')]
                    ranks_info = []
                    for artist in artists:
                        if not artist: continue
                        rank = top_100_artists_lookup.get(artist.strip(), '-')
                        ranks_info.append(f"{artist.strip()} (Rank: {rank})")
                    # ***** 修改点: 使用 ', ' 作为分隔符 *****
                    return ", ".join(ranks_info) if ranks_info else "-"
                    # ***************************************

                # --- Apply Function to Add Column ---
                # Ensure 'Artists' column exists before applying
                if 'Artists' in ranked_df.columns:
                    ranked_df['Artist(s) (Top 100 Rank)'] = ranked_df['Artists'].apply(find_song_artist_ranks_export)
                else:
                    logger.warning("[Export] 'Artists' column not found in ranked songs df, cannot add ranks.")
                    ranked_df['Artist(s) (Top 100 Rank)'] = '-'

            ranked_df_augmented = ranked_df # Assign augmented df

        # --- 3. Format and Return File ---
        if ranked_df_augmented.empty:
             return jsonify({'error': f'Failed to generate augmented {export_type} data for export.'}), 500

        output_filename = f"export_{export_type}_{source_name}_top100.{export_format}"
        output_filename = "".join(c for c in output_filename if c.isalnum() or c in ['.', '_', '-']).rstrip()

        # ***** 修改点: 在导出前替换 NaN *****
        ranked_df_export = ranked_df_augmented.replace({np.nan: None}) # Use None for CSV/Excel consistency
        # ************************************

        if export_format == 'csv':
            try:
                csv_data = ranked_df_export.to_csv(index=False, encoding='utf-8-sig')
                response = make_response(csv_data)
                response.headers['Content-Disposition'] = f'attachment; filename="{output_filename}"'
                response.headers['Content-Type'] = 'text/csv; charset=utf-8'
                logger.info(f"Exporting {export_type} ranking as CSV: {output_filename}")
                return response
            except Exception as csv_error:
                 logger.exception(f"Error generating CSV file: {csv_error}")
                 return jsonify({'error': f'Failed to generate CSV file: {csv_error}'}), 500

        elif export_format == 'xlsx':
            try:
                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                    # Replace None with empty string for Excel if preferred, or keep None
                    ranked_df_export.fillna('').to_excel(writer, index=False, sheet_name=export_type.capitalize())
                output_buffer.seek(0)
                logger.info(f"Exporting {export_type} ranking as XLSX: {output_filename}")
                return send_file(
                    output_buffer, as_attachment=True, download_name=output_filename,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            except ImportError: logger.error("Exporting as XLSX requires 'openpyxl'."); return jsonify({'error': "Server configuration error: XLSX export requires 'openpyxl'. Please install it (`pip install openpyxl`)."}), 500
            except Exception as excel_error: logger.exception(f"Error generating XLSX file: {excel_error}"); return jsonify({'error': f'Failed to generate XLSX file: {excel_error}'}), 500

    # --- General Error Handling ---
    except FileNotFoundError: return jsonify({'error': 'File not found on server. Please upload again.'}), 404
    except ValueError as e: logger.warning(f"ValueError during export generation: {e}"); return jsonify({'error': str(e)}), 400
    except Exception as e: logger.exception(f"Unexpected error during export for {filename}, type {export_type}: {str(e)}"); return jsonify({'error': f'Failed to generate export file: {str(e)}'}), 500
    
    # --- 新增: Spotify 歌单生成路由 ---
@analysis_bp.route('/playlist/spotify/top_songs', methods=['GET'])
def generate_spotify_playlist():
    """
    Generates a list of Spotify track URIs based on the top songs ranking.
    Query Parameters:
        file (str): The name of the uploaded data file. Required.
    """
    filename = request.args.get('file')

    # --- Input Validation ---
    if not filename:
        return jsonify({'error': 'Missing required parameter: file'}), 400

    # --- File Handling ---
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    file_ext = get_file_extension(filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on server. Please upload again.'}), 404

    try:
        # --- Read Data ---
        df, source_name = read_datafile(file_path, file_ext)

        # --- Get Ranked Songs Data ---
        # 使用 utils 中的函数获取完整的排名 DataFrame
        # 假设 get_ranked_songs_df 会返回一个包含 'Spotify ID' 列的 DataFrame
        # (如果原始列名是 spotify_id, 它在 get_ranked_songs_df 中可能被重命名了)
        ranked_df = get_ranked_songs_df(df)

        if ranked_df.empty:
            return jsonify({'error': 'Could not generate song ranking. Check data or server logs.'}), 400

        # --- Extract Spotify IDs and Format URIs ---
        # 确定 Spotify ID 列名 (可能在 get_ranked_songs_df 中被重命名为 'Spotify ID')
        spotify_id_column_name = None
        if 'Spotify ID' in ranked_df.columns:
            spotify_id_column_name = 'Spotify ID'
        elif 'spotify_id' in ranked_df.columns: # Fallback to original name if rename didn't happen
             spotify_id_column_name = 'spotify_id'

        if not spotify_id_column_name:
             return jsonify({'error': 'Spotify ID column not found in the ranked song data.'}), 400

        # 获取 Spotify ID 列表，移除空值或无效值
        spotify_ids = ranked_df[spotify_id_column_name].dropna().astype(str).unique()
        valid_spotify_ids = [sid for sid in spotify_ids if sid and isinstance(sid, str) and len(sid.strip()) > 0 and sid.lower() != 'nan' and sid.lower() != 'none'] # Basic validation

        if not valid_spotify_ids:
            return jsonify({'error': 'No valid Spotify IDs found in the top songs list.'}), 400

        # 格式化为 Spotify URI
        spotify_uris = [f"spotify:track:{sid.strip()}" for sid in valid_spotify_ids]

        logger.info(f"Generated Spotify URI list with {len(spotify_uris)} tracks for file {filename}.")

        # 返回 URI 列表
        return jsonify({'uris': spotify_uris})

    # --- Error Handling ---
    except FileNotFoundError:
        return jsonify({'error': 'File not found on server. Please upload again.'}), 404
    except ValueError as e: # Catch ValueErrors from utils (e.g., missing columns)
        logger.warning(f"ValueError during Spotify playlist generation: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Unexpected error during Spotify playlist generation for {filename}: {str(e)}")
        return jsonify({'error': f'Failed to generate Spotify playlist: {str(e)}'}), 500


