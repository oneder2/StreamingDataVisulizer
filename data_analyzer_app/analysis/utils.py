# data_analyzer_app/analysis/utils.py
import pandas as pd
import numpy as np
import os
import logging
from sklearn.preprocessing import MinMaxScaler

# Use standard logging; configuration should be handled by the app factory
logger = logging.getLogger(__name__)

# --- File and String Helpers (保持不变) ---

def find_first_data_sheet(sheet_names):
    """Finds the first sheet name that is not 'Dictionary' (case-insensitive)."""
    for sheet in sheet_names:
        if sheet.lower() != 'dictionary':
            return sheet
    return None

def safe_str_lower(val):
    """Safely convert value to lowercase string, handling non-string types."""
    try:
        return str(val).lower()
    except Exception as e:
        logger.debug(f"Could not convert value to lowercase string: {val}, Error: {e}")
        return ""

def get_file_extension(filename):
    """Gets the lowercased file extension."""
    if filename:
        return os.path.splitext(filename)[1].lower()
    return ""

def read_datafile(file_path, file_ext):
    """Reads data from Excel (first non-dict sheet) or CSV."""
    df = None
    source_name = os.path.basename(file_path)

    if file_ext in ['.xlsx', '.xls']:
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            data_sheet_name = find_first_data_sheet(sheet_names)
            if not data_sheet_name:
                raise ValueError("No data sheet (non-Dictionary) found in Excel file.")
            logger.info(f"Reading data from Excel sheet: {data_sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=data_sheet_name)
            source_name = data_sheet_name # Use sheet name as source if Excel
        except Exception as e:
            logger.error(f"Error reading Excel file {os.path.basename(file_path)}: {e}")
            raise ValueError(f"Failed to read Excel file '{os.path.basename(file_path)}'. It might be corrupted or password-protected.") from e
    elif file_ext == '.csv':
        logger.info(f"Reading data from CSV file: {source_name}")
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            logger.warning("UTF-8 CSV decoding failed, trying 'latin1'.")
            try:
                df = pd.read_csv(file_path, encoding='latin1')
            except Exception as e_latin:
                 logger.error(f"Error reading CSV file {source_name} with latin1 encoding: {e_latin}")
                 raise ValueError(f"Failed to read CSV file '{source_name}' with UTF-8 or latin1 encoding.") from e_latin
        except Exception as e_csv:
            logger.error(f"Error reading CSV file {source_name}: {e_csv}")
            raise ValueError(f"Failed to read CSV file '{source_name}'. Check format and encoding.") from e_csv
    else:
        raise ValueError(f"Unsupported file type '{file_ext}'.")

    if df is None:
        raise ValueError("Could not load data frame.")

    logger.info(f"Successfully read data from {source_name}")
    return df, source_name


# --- Single Column Analysis Logic (保持不变) ---

def detect_and_process_boolean(target_series, norm_weights=None):
    """Detects if a series is boolean-like and calculates (weighted) counts."""
    is_boolean = False; true_vals, false_vals = 0, 0
    true_patterns = { 'true', 'yes', '1', 't', 'y', '是', '真' }; false_patterns = { 'false', 'no', '0', 'f', 'n', '否', '假' }
    try:
        str_col = target_series.dropna().astype(str).str.lower().str.strip(); unique_vals = set(str_col.unique())
        if unique_vals.difference(['']).issubset(true_patterns.union(false_patterns)):
            is_boolean = True; target_series_non_na = target_series.dropna()
            bool_as_01 = target_series_non_na.astype(str).str.lower().str.strip().isin(true_patterns).astype(int)
            if norm_weights is not None:
                if len(target_series_non_na) == len(norm_weights):
                    true_vals = np.sum(bool_as_01 * norm_weights); false_vals = np.sum((1 - bool_as_01) * norm_weights)
                else: logger.warning(f"Length mismatch boolean ({len(target_series_non_na)}) vs weights ({len(norm_weights)}). Unweighted."); true_vals = bool_as_01.sum(); false_vals = len(target_series_non_na) - true_vals
            else: true_vals = bool_as_01.sum(); false_vals = len(target_series_non_na) - true_vals
            logger.debug(f"Column processed as boolean."); return True, {'true': float(true_vals), 'false': float(false_vals)}
        else: logger.debug(f"Column unique values not exclusively boolean patterns: {unique_vals}"); return False, None
    except Exception as e: logger.warning(f"Error during boolean check: {e}. Assuming not boolean."); return False, None

def calculate_numeric_stats_histogram(valid_data, final_weights=None):
    """Calculates statistics and histogram for numeric data (weighted or unweighted)."""
    stats = {}; histogram_data = {}
    if valid_data.empty: logger.warning("Cannot calculate numeric stats: input data is empty."); return stats, histogram_data
    valid_data = pd.to_numeric(valid_data, errors='coerce').dropna()
    if valid_data.empty: logger.warning("Cannot calculate numeric stats: no valid numeric data after coercion."); return stats, histogram_data
    data_min = valid_data.min(); data_max = valid_data.max()
    try:
        if final_weights is not None:
             if len(final_weights) != len(valid_data): logger.error(f"Weight length ({len(final_weights)}) != Data length ({len(valid_data)}) for stats. Using unweighted."); final_weights = None
             elif not (np.sum(final_weights) > 1e-9 and np.isfinite(np.sum(final_weights))): logger.warning(f"Sum of final weights is zero or non-finite ({np.sum(final_weights)}). Using equal weights."); final_weights = np.ones(len(valid_data)) / len(valid_data)
        if final_weights is not None:
             w_mean = np.average(valid_data, weights=final_weights); w_var = np.average((valid_data - w_mean)**2, weights=final_weights); w_std = np.sqrt(w_var)
             desc = valid_data.describe(percentiles=[.25, .5, .75])
             stats = { 'count': len(valid_data), 'mean': float(w_mean), 'std': float(w_std), 'min': float(data_min), 'q1': float(desc.get('25%', np.nan)), 'median': float(desc.get('50%', np.nan)), 'q3': float(desc.get('75%', np.nan)), 'max': float(data_max), 'variance': float(w_var) }; logger.debug("Calculated weighted numeric stats (quantiles unweighted).")
        else:
             desc = valid_data.describe(percentiles=[.25, .5, .75])
             stats = { 'count': int(desc.get('count', 0)), 'mean': float(desc.get('mean', np.nan)), 'std': float(desc.get('std', np.nan)), 'min': float(data_min), 'q1': float(desc.get('25%', np.nan)), 'median': float(desc.get('50%', np.nan)), 'q3': float(desc.get('75%', np.nan)), 'max': float(data_max), 'variance': float(valid_data.var(ddof=0)) if len(valid_data) > 0 else np.nan }; logger.debug("Calculated unweighted numeric stats.")
        num_bins = 10; hist_range = None;
        if data_min < data_max: hist_range = (data_min, data_max)
        elif data_min == data_max: delta = abs(data_min * 0.1) if data_min != 0 else 0.1; hist_range = (data_min - delta, data_max + delta); num_bins = 1
        if final_weights is not None and len(final_weights) != len(valid_data): logger.error(f"Weight length ({len(final_weights)}) != Data length ({len(valid_data)}) for histogram. Using unweighted."); final_weights = None
        hist, bin_edges = np.histogram(valid_data, bins=num_bins, range=hist_range, weights=final_weights)
        if len(bin_edges) > 1: labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(hist))]
        else: labels = [f"{data_min:.2f}"] if len(hist) == 1 else []
        histogram_data = { 'labels': labels, 'values': hist.tolist() }; logger.debug("Calculated histogram.")
    except Exception as e: logger.error(f"Error calculating numeric stats/histogram: {e}", exc_info=True); stats = {}; histogram_data = {}
    return stats, histogram_data


# --- Artist Ranking Logic Helpers (保持不变) ---

def weighted_avg(x, col_name, weight_col='weight'):
    """Helper function to calculate weighted average within a group (used by apply)."""
    artist_name = x.name if isinstance(x.name, str) else "Group"; 
    try:
        if col_name not in x.columns or weight_col not in x.columns: logger.warning(f"Weighted avg: Column '{col_name}' or '{weight_col}' not found for group '{artist_name}'."); return np.nan
        subset_df = x[[col_name, weight_col]].dropna(); 
        if subset_df.empty: logger.debug(f"Weighted avg for '{artist_name}', col '{col_name}': No data after initial dropna on value/weight."); return np.nan
        data = pd.to_numeric(subset_df[col_name], errors='coerce'); weights = subset_df[weight_col]; mask = data.notna(); data_valid = data[mask]; weights_valid = weights[mask]
        valid_count = len(data_valid); sum_weights_valid = weights_valid.sum(); log_msg = f"Weighted avg for '{artist_name}', col '{col_name}': ValidCount={valid_count}, SumWeights={sum_weights_valid:.4f}"
        if sum_weights_valid > 1e-9 and np.isfinite(sum_weights_valid) and valid_count > 0: result = np.average(data_valid, weights=weights_valid); logger.debug(f"{log_msg} -> Result={result:.4f}"); return result
        else: logger.warning(f"{log_msg} -> Returning NaN (invalid weights or no data)."); return np.nan
    except Exception as e: logger.error(f"Error calculating weighted avg for group '{artist_name}', col '{col_name}': {e}", exc_info=False); return np.nan

def get_top_track_name(group):
    """Helper function to find the top track name within a group (used by apply)."""
    artist_name = group.name if isinstance(group.name, str) else "Group"; 
    try:
        if 'popularity' not in group.columns or 'name' not in group.columns: logger.warning(f"Missing 'popularity' or 'name' column for group {artist_name}"); return "N/A"
        valid_popularity_group = group.dropna(subset=['popularity']); 
        if not valid_popularity_group.empty:
            numeric_popularity = pd.to_numeric(valid_popularity_group['popularity'], errors='coerce'); valid_numeric_popularity = numeric_popularity.dropna()
            if not valid_numeric_popularity.empty:
                top_track_idx = valid_numeric_popularity.idxmax()
                if top_track_idx in group.index: return group.loc[top_track_idx, 'name']
                else: logger.warning(f"idxmax index {top_track_idx} not found in group for {artist_name}. Falling back.")
            else: logger.warning(f"No valid numeric popularity found for {artist_name}. Falling back.")
        most_frequent = group['name'].mode(); fallback_name = most_frequent.iloc[0] if not most_frequent.empty else "N/A"
        logger.debug(f"Falling back to most frequent track name for {artist_name}: {fallback_name}"); return fallback_name
    except Exception as e: logger.error(f"Error finding top track for {artist_name}: {e}", exc_info=False); return "Error"

def calculate_artist_metrics(group):
    """Calculates all metrics for a single artist group (used with apply)."""
    metrics = {}; artist_name = group.name if isinstance(group.name, str) else "Group"; required_cols_group = ['weight', 'popularity', 'loudness', 'name']
    metrics['total_weight'] = 0; metrics['avg_popularity'] = np.nan; metrics['avg_loudness'] = np.nan; metrics['song_count'] = 0; metrics['entry_count'] = len(group); metrics['top_track_name'] = "N/A"
    if not all(col in group.columns for col in required_cols_group): logger.warning(f"Group {artist_name} missing required columns for metric calculation."); return pd.Series(metrics)
    try:
        metrics['total_weight'] = group['weight'].sum(); metrics['avg_popularity'] = weighted_avg(group, 'popularity'); metrics['avg_loudness'] = weighted_avg(group, 'loudness'); metrics['song_count'] = group['name'].nunique(); metrics['top_track_name'] = get_top_track_name(group)
    except Exception as e: logger.error(f"Error calculating metrics for group {artist_name}: {e}", exc_info=True); metrics['total_weight'] = 0; metrics['avg_popularity'] = np.nan; metrics['avg_loudness'] = np.nan; metrics['song_count'] = 0; metrics['top_track_name'] = "Error"
    return pd.Series(metrics)


# --- NEW: Function to get FULL ranked artists DataFrame ---
def get_ranked_artists_df(df):
    """Processes the DataFrame to calculate and return the fully ranked artist list."""
    logger.info("Starting full artist ranking calculation."); required_cols = ['artists', 'daily_rank', 'name', 'popularity', 'loudness']
    missing_cols = [col for col in required_cols if col not in df.columns]; 
    if missing_cols: raise ValueError(f'Missing required columns for artist ranking: {", ".join(missing_cols)}')
    try:
        df_processed = df.copy(); df_processed['artists'] = df_processed['artists'].astype(str).fillna(''); df_processed['artists_list'] = df_processed['artists'].str.split(r'\s*,\s*')
        df_exploded = df_processed.explode('artists_list'); df_exploded = df_exploded.rename(columns={'artists_list': 'artist_name'}); df_exploded['artist_name'] = df_exploded['artist_name'].str.strip(); df_exploded = df_exploded[df_exploded['artist_name'] != '']
        if df_exploded.empty: logger.warning('No valid artist data found after exploding/cleaning.'); return pd.DataFrame()
        df_exploded['daily_rank'] = pd.to_numeric(df_exploded['daily_rank'], errors='coerce'); df_exploded = df_exploded.dropna(subset=['daily_rank']); df_exploded = df_exploded[df_exploded['daily_rank'] > 0]
        if df_exploded.empty: logger.warning('No valid positive daily ranks found for weighting.'); return pd.DataFrame()
        df_exploded['weight'] = 1 / (df_exploded['daily_rank'] ** 2)
        logger.info("Grouping by artist name and calculating metrics..."); grouped = df_exploded.groupby('artist_name'); final_results = grouped.apply(calculate_artist_metrics)
        if final_results.empty: logger.warning("No results after grouping and applying metrics."); return pd.DataFrame()
        final_results = final_results.sort_values('total_weight', ascending=False); final_results = final_results.reset_index(); final_results['rank'] = final_results.index + 1
        output_cols_map = {'rank': 'Rank', 'artist_name': 'Artist', 'top_track_name': 'Top Track', 'avg_popularity': 'Avg Popularity', 'avg_loudness': 'Avg Loudness', 'total_weight': 'Score', 'song_count': 'Unique Songs', 'entry_count': 'Total Entries'}
        cols_to_select = [col for col in output_cols_map.keys() if col in final_results.columns]; ranked_df = final_results[cols_to_select].rename(columns=output_cols_map)
        logger.info(f"Successfully calculated full ranking for {len(ranked_df)} artists."); return ranked_df
    except Exception as e: logger.exception(f"Error during full artist ranking calculation: {e}"); return pd.DataFrame()


# --- NEW: Function to get FULL ranked songs DataFrame ---
def get_ranked_songs_df(df):
    """
    Processes the DataFrame to calculate and return the fully ranked song list.
    Ensures the identifier column (Spotify ID or Name) is present in the output.
    """
    logger.info("Starting full song ranking calculation.")
    df_processed = df.copy()

    # --- Determine Song Identifier ---
    song_id_col = None
    has_spotify_id = 'spotify_id' in df_processed.columns
    has_name = 'name' in df_processed.columns

    if has_spotify_id:
         # Check if spotify_id column has enough non-null values to be useful
         if df_processed['spotify_id'].notna().sum() > 0:
             song_id_col = 'spotify_id'
             df_processed = df_processed.dropna(subset=['spotify_id']) # Drop rows with missing ID if using it
             df_processed[song_id_col] = df_processed[song_id_col].astype(str).str.strip() # Clean ID
             logger.info("Using 'spotify_id' as song identifier.")
         elif has_name: # Fallback to name if spotify_id is present but mostly null
             song_id_col = 'name'
             df_processed[song_id_col] = df_processed[song_id_col].astype(str).str.strip().str.lower() # Clean Name
             logger.warning("Column 'spotify_id' found but contains too many nulls. Using 'name' (lower, stripped) as song identifier.")
         else:
              raise ValueError('Missing required columns: Need usable "spotify_id" or "name" to identify songs.')
    elif has_name:
         song_id_col = 'name'
         df_processed[song_id_col] = df_processed[song_id_col].astype(str).str.strip().str.lower() # Clean Name
         logger.warning("Column 'spotify_id' not found. Using 'name' (lower, stripped) as song identifier.")
    else:
         raise ValueError('Missing required columns: Need either "spotify_id" or "name" to identify songs.')

    # --- Verify Required Columns ---
    required_cols = [song_id_col, 'artists', 'album_name', 'popularity', 'loudness', 'daily_rank']
    if 'name' not in required_cols: required_cols.append('name') # Always need name for display
    missing_cols = [col for col in required_cols if col not in df_processed.columns]
    if missing_cols: raise ValueError(f'Missing required columns for song ranking: {", ".join(missing_cols)}')

    try:
        # --- Data Preparation (Weight Calculation) ---
        df_processed['daily_rank'] = pd.to_numeric(df_processed['daily_rank'], errors='coerce')
        df_processed = df_processed.dropna(subset=['daily_rank'])
        df_processed = df_processed[df_processed['daily_rank'] > 0]
        if df_processed.empty: logger.warning('No valid positive daily ranks found for weighting songs.'); return pd.DataFrame()
        df_processed['weight'] = 1 / (df_processed['daily_rank'] ** 2)

        # --- Group by Song and Aggregate ---
        logger.info(f"Grouping by song identifier '{song_id_col}' and aggregating...")
        grouped = df_processed.groupby(song_id_col)

        agg_funcs = {
            'total_weight': pd.NamedAgg(column='weight', aggfunc='sum'),
            'name': pd.NamedAgg(column='name', aggfunc='first'), # Always get first name
            'artists': pd.NamedAgg(column='artists', aggfunc='first'),
            'album_name': pd.NamedAgg(column='album_name', aggfunc='first'),
            'avg_popularity': pd.NamedAgg(column='popularity', aggfunc=lambda x: pd.to_numeric(x, errors='coerce').mean()),
            'avg_loudness': pd.NamedAgg(column='loudness', aggfunc=lambda x: pd.to_numeric(x, errors='coerce').mean()),
            'entry_count': pd.NamedAgg(column=song_id_col, aggfunc='size')
        }
        # If grouping by name, remove duplicate name aggregation
        if song_id_col == 'name': del agg_funcs['name']

        agg_results = grouped.agg(**agg_funcs)

        # --- Ensure Identifier Column is Present ---
        # If grouped by 'spotify_id', reset index to make 'spotify_id' a column
        # If grouped by 'name', the index IS the name, add it as a column
        if song_id_col == 'spotify_id':
            agg_results = agg_results.reset_index() # spotify_id becomes a column
        elif song_id_col == 'name':
             if 'name' not in agg_results.columns: # Should not happen based on agg_funcs logic
                 agg_results['name'] = agg_results.index # Add name from index

        if agg_results.empty: logger.warning("No results after grouping and aggregating songs."); return pd.DataFrame()

        # --- Rank ALL Songs ---
        agg_results = agg_results.sort_values('total_weight', ascending=False).reset_index(drop=True) # Reset index after sort
        agg_results['rank'] = agg_results.index + 1

        # --- Final Column Selection and Renaming ---
        # Define the columns we absolutely want in the final output for consistency
        final_columns_map = {
            'rank': 'Rank',
            'name': 'Name',
            'artists': 'Artists',
            'album_name': 'Album',
            'avg_popularity': 'Popularity',
            'avg_loudness': 'Loudness',
            'total_weight': 'Score'
            # Conditionally add Spotify ID if it was used and exists
        }
        if song_id_col == 'spotify_id' and 'spotify_id' in agg_results.columns:
            final_columns_map['spotify_id'] = 'Spotify ID'

        # Select and rename columns that exist in agg_results
        cols_to_select = [col for col in final_columns_map.keys() if col in agg_results.columns]
        if not cols_to_select: logger.error("No columns selected for ranked songs output!"); return pd.DataFrame()

        ranked_df = agg_results[cols_to_select].rename(columns=final_columns_map)

        # Ensure required columns ('Rank', 'Name', 'Artists', 'Spotify ID' if used) are present
        if 'Rank' not in ranked_df.columns: ranked_df['Rank'] = np.nan # Should not happen
        if 'Name' not in ranked_df.columns: ranked_df['Name'] = 'N/A'
        if 'Artists' not in ranked_df.columns: ranked_df['Artists'] = 'N/A'
        if song_id_col == 'spotify_id' and 'Spotify ID' not in ranked_df.columns:
             logger.warning("Spotify ID column missing in final ranked songs DataFrame despite being the identifier.")
             # Try adding it back from index if reset_index failed somehow? Unlikely.
             # ranked_df['Spotify ID'] = agg_results['spotify_id'] # Risky if lengths mismatch

        logger.info(f"Successfully calculated full ranking for {len(ranked_df)} songs.")
        return ranked_df

    except Exception as e:
        logger.exception(f"Error during full song ranking calculation: {e}")
        return pd.DataFrame()
