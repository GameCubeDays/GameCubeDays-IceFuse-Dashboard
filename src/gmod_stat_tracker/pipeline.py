import pandas as pd
import time
from datetime import datetime, timedelta
import os
import pickle
from typing import Tuple
import gspread
from google.oauth2.service_account import Credentials
import re

# Import from our own package modules (Absolute Imports)
from gmod_stat_tracker.battlemetrics_scraper import (
    login_to_battlemetrics,
    scrape_multiple_weeks
)
from gmod_stat_tracker.roster_manager import (
    get_steam_ids_from_google_sheet,
    resolve_steam_ids_to_names
)
from gmod_stat_tracker.gmod_api_fetcher import fetch_gmod_leaderboard

# Import all configuration from config.py
from gmod_stat_tracker import config

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException


def detect_and_warn_outliers(df):
    """(Unchanged logic)"""
    print("\n" + "="*60)
    print("DATA QUALITY CHECK - DETECTING OUTLIERS")
    print("="*60)
    
    df = df.copy()
    df['Has_Outlier'] = False
    outlier_count = 0
    
    for idx, row in df.iterrows():
        player_name = row.get('SteamName_Current', 'Unknown')
        issues = []
        
        # Check Headshot % (should be 0-100)
        if 'HS_Percent' in row and pd.notna(row['HS_Percent']) and str(row['HS_Percent']).strip() != '':
            try:
                hs_pct = float(row['HS_Percent'])
                if hs_pct > 100:
                    issues.append(f"Headshot % = {hs_pct:.2f}% (over 100%)")
                    df.at[idx, 'Has_Outlier'] = True
            except (ValueError, TypeError):
                pass
        
        # Check K/D Ratio (reasonable range 0-10)
        if 'KD_Ratio' in row and pd.notna(row['KD_Ratio']) and str(row['KD_Ratio']).strip() != '':
            try:
                kd = float(row['KD_Ratio'])
                if kd > 10:
                    issues.append(f"K/D Ratio = {kd:.2f} (over 10)")
                    df.at[idx, 'Has_Outlier'] = True
            except (ValueError, TypeError):
                pass
        
        # Check for negative values
        for col in ['Kills', 'Deaths', 'Money', 'Level']:
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != '':
                try:
                    val = float(row[col])
                    if val < 0:
                        issues.append(f"{col} = {val} (negative)")
                        df.at[idx, 'Has_Outlier'] = True
                except (ValueError, TypeError):
                    pass
        
        if issues:
            outlier_count += 1
            print(f"⚠️ Player: {player_name}")
            for issue in issues:
                print(f"   - {issue}")
    
    if outlier_count == 0:
        print("✅ No outliers detected!")
    else:
        print(f"\n⚠️ Found {outlier_count} player(s) with outliers")
        print("   These players are EXCLUDED from pivot tables and graphs")
        print("   but INCLUDED in Player_Report for your review")
    
    print("="*60)
    
    return df

def format_date_range_short(date_range_str):
    """(Unchanged logic)"""
    try:
        parts = date_range_str.split(' - ')
        if len(parts) == 2:
            start_date = datetime.strptime(parts[0], '%Y-%m-%d %H:%M')
            end_date = datetime.strptime(parts[1], '%Y-%m-%d %H:%M')
            return f"{start_date.strftime('%m/%d')} - {end_date.strftime('%m/%d')}"
    except:
        pass
    return date_range_str

def parse_playtime_to_hours(time_str):
    """(Unchanged logic)"""
    if pd.isna(time_str) or time_str == '':
        return 0.0
    
    time_str = str(time_str).strip()
    
    if 'h' in time_str or 'd' in time_str:
        total_hours = 0.0
        
        days_match = re.search(r'(\d+)d', time_str)
        if days_match:
            total_hours += int(days_match.group(1)) * 24
        
        hours_match = re.search(r'(\d+)h', time_str)
        if hours_match:
            total_hours += int(hours_match.group(1))
        
        minutes_match = re.search(r'(\d+)m', time_str)
        if minutes_match:
            total_hours += int(minutes_match.group(1)) / 60.0
        
        return round(total_hours, 2)
    
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            try:
                hours = int(parts[0])
                minutes = int(parts[1])
                return round(hours + minutes / 60.0, 2)
            except ValueError:
                return 0.0
    
    return 0.0

def safe_float(value):
    """(Unchanged logic)"""
    try:
        return float(value) if pd.notna(value) and value != '' else 0.0
    except (ValueError, TypeError):
        return 0.0

def calculate_roster_fields(row):
    """(Unchanged logic)"""
    branch = "Unknown"
    sub_branch = "None"
    
    for index, branch_name in config.BRANCH_MAPPING.items():
        col_name = f'Col_{index}_Member'
        if index <= 4 and row.get(col_name) == True:
            branch = branch_name
            break

    sub_branches = []
    for index, sub_branch_name in config.SUB_BRANCH_MAPPING.items():
        col_name = f'Col_{index}_Member'
        if index >= 5 and row.get(col_name) == True:
            sub_branches.append(sub_branch_name)
    
    if sub_branches:
        sub_branch = ", ".join(sub_branches)
    
    return branch, sub_branch

# --- CACHE ---

def _ensure_cache_dir():
    """Helper to create cache directory."""
    if not os.path.exists(config.CACHE_DIR):
        os.makedirs(config.CACHE_DIR)

def load_or_scrape_data(driver):
    """(Unchanged logic, uses config paths)"""
    _ensure_cache_dir() # Ensure cache dir exists
    
    if os.path.exists(config.CACHE_FILENAME):
        cache_time = datetime.fromtimestamp(os.path.getmtime(config.CACHE_FILENAME))
        if datetime.now() - cache_time < timedelta(hours=config.CACHE_EXPIRY_HOURS):
            print(f"Cache found. Loading from cache...")
            with open(config.CACHE_FILENAME, 'rb') as f:
                return pickle.load(f)
        else:
            print("Cache expired. Starting new scrape...")
    else:
        print("No cache found. Starting scrape...")

    # Use credentials from config
    if not login_to_battlemetrics(driver, config.BATTLEMETRICS_USERNAME, config.BATTLEMETRICS_PASSWORD):
        raise ConnectionError("Login failed.")

    scraped_df = scrape_multiple_weeks(driver, config.BASE_LEADERBOARD_URL, config.WEEKS_TO_PULL)
    
    if not scraped_df.empty:
        with open(config.CACHE_FILENAME, 'wb') as f:
            pickle.dump(scraped_df, f)
        print(f"Scraped data saved to cache.")
    
    return scraped_df

# --- GOOGLE SHEETS UPLOAD ---

def upload_to_google_sheets(df, sheet_id, tab_name, creds_file, format_dates=False):
    """(Unchanged logic)"""
    print(f"\n[UPLOADING TO GOOGLE SHEETS: {tab_name}]")
    print(f"DataFrame shape: {df.shape}")
    
    df_upload = df.copy()
    
    if format_dates:
        # Note: '2025' is hardcoded in your original logic.
        date_columns = [col for col in df_upload.columns if ' - ' in str(col) and '2025' in str(col)] 
        if date_columns:
            print(f"Formatting {len(date_columns)} date columns...")
            rename_map = {col: format_date_range_short(col) for col in date_columns}
            df_upload = df_upload.rename(columns=rename_map)
    
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(creds_file, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key(sheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(tab_name)
            print(f"Found existing tab. Clearing...")
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            print(f"Creating new tab...")
            worksheet = spreadsheet.add_worksheet(title=tab_name, rows=5000, cols=50)
        
        headers = df_upload.columns.values.tolist()
        data_rows = df_upload.values.tolist()
        
        data_rows = [['' if pd.isna(cell) else cell for cell in row] for row in data_rows]
        
        print(f"Uploading {len(data_rows)} data rows...")
        
        worksheet.update(range_name='A1', values=[headers])
        
        if len(data_rows) > 0:
            worksheet.update(range_name='A2', values=data_rows)
        
        print(f"✅ Upload complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- PIVOT CALCULATIONS ---

def calculate_branch_pivots(pivot_df):
    """(Unchanged logic, uses config.BRANCH_MAPPING)"""
    print("\n[CALCULATING BRANCH PIVOT STATISTICS]")
    
    # Filter out outliers
    if 'Has_Outlier' in pivot_df.columns:
        clean_df = pivot_df[pivot_df['Has_Outlier'] == False].copy()
        outlier_count = len(pivot_df) - len(clean_df)
        if outlier_count > 0:
            print(f"   Excluding {outlier_count} player(s) with outliers from pivot")
    else:
        clean_df = pivot_df.copy()
    
    main_branches = ['Army', 'USAF', 'USMC', 'NAVY']
    branch_data = clean_df[clean_df['Branch'].isin(main_branches)].copy()
    
    if branch_data.empty:
        print("⚠️ No data found for main branches.")
        return pd.DataFrame()
    
    week_columns = [col for col in branch_data.columns if ' - ' in str(col)]
    
    print(f"Processing {len(branch_data)} player records (outliers excluded)")
    print(f"Found {len(week_columns)} week columns")
    
    all_branch_data = []
    
    for branch in main_branches:
        branch_players = branch_data[branch_data['Branch'] == branch]
        row_data = {'Branch': branch}
        
        stats_columns = {
            'Avg_KD_Ratio': 'KD_Ratio',
            'Avg_HS_Percent': 'HS_Percent',
            'Avg_Kills': 'Kills',
            'Avg_Deaths': 'Deaths',
            'Avg_Level': 'Level',
            'Avg_Money': 'Money',
            'Avg_Damage': 'Damage',
            'Avg_Headshots': 'Headshots'
        }
        
        for stat_name, column_name in stats_columns.items():
            if column_name in branch_players.columns:
                values = branch_players[column_name].apply(safe_float)
                values = values[values > 0]
                
                if len(values) > 0:
                    avg_value = values.mean()
                    row_data[stat_name] = round(avg_value, 2)
                else:
                    row_data[stat_name] = 0.0
            else:
                row_data[stat_name] = 0.0
        
        for week_col in week_columns:
            playtime_values = branch_players[week_col].dropna()
            
            if len(playtime_values) > 0:
                hours_list = [parse_playtime_to_hours(val) for val in playtime_values]
                hours_list = [h for h in hours_list if h > 0]
                
                if hours_list:
                    avg_hours = sum(hours_list) / len(hours_list)
                    row_data[week_col] = round(avg_hours, 2)
                else:
                    row_data[week_col] = 0.0
            else:
                row_data[week_col] = 0.0
        
        all_branch_data.append(row_data)
    
    result_df = pd.DataFrame(all_branch_data)
    
    stat_cols = ['Branch', 'Avg_KD_Ratio', 'Avg_HS_Percent', 'Avg_Kills', 'Avg_Deaths', 
                 'Avg_Level', 'Avg_Money', 'Avg_Damage', 'Avg_Headshots']
    week_cols_sorted = sorted([col for col in result_df.columns if ' - ' in str(col)])
    
    final_cols = stat_cols + week_cols_sorted
    result_df = result_df[[col for col in final_cols if col in result_df.columns]]
    
    print(f"✅ Created branch pivots: {len(result_df)} branches")
    
    return result_df


def calculate_subbranch_pivots(pivot_df, roster_membership_df):
    """(Unchanged logic, uses config.SUB_BRANCH_MAPPING)"""
    print("\n[CALCULATING SUB-BRANCH PIVOT STATISTICS]")
    
    # Filter out outliers
    if 'Has_Outlier' in pivot_df.columns:
        clean_df = pivot_df[pivot_df['Has_Outlier'] == False].copy()
        outlier_count = len(pivot_df) - len(clean_df)
        if outlier_count > 0:
            print(f"   Excluding {outlier_count} player(s) with outliers from pivot")
    else:
        clean_df = pivot_df.copy()
    
    week_columns = [col for col in clean_df.columns if ' - ' in str(col)]
    
    analysis_df = clean_df.merge(
        roster_membership_df[[f'Col_{i}_Member' for i in config.SUB_BRANCH_MAPPING.keys()] + ['SteamID64']], 
        on='SteamID64', 
        how='left'
    )
    
    all_subbranch_data = []
    
    for col_index, subbranch_name in config.SUB_BRANCH_MAPPING.items():
        col_name = f'Col_{col_index}_Member'
        
        subbranch_players = analysis_df[analysis_df[col_name] == True].copy()
        
        if len(subbranch_players) == 0:
            continue
        
        row_data = {'SubBranch': subbranch_name}
        
        stats_columns = {
            'Avg_KD_Ratio': 'KD_Ratio',
            'Avg_HS_Percent': 'HS_Percent',
            'Avg_Kills': 'Kills',
            'Avg_Deaths': 'Deaths',
            'Avg_Level': 'Level',
            'Avg_Money': 'Money',
            'Avg_Damage': 'Damage',
            'Avg_Headshots': 'Headshots'
        }
        
        for stat_name, column_name in stats_columns.items():
            if column_name in subbranch_players.columns:
                values = subbranch_players[column_name].apply(safe_float)
                values = values[values > 0]
                
                if len(values) > 0:
                    avg_value = values.mean()
                    row_data[stat_name] = round(avg_value, 2)
                else:
                    row_data[stat_name] = 0.0
            else:
                row_data[stat_name] = 0.0
        
        for week_col in week_columns:
            playtime_values = subbranch_players[week_col].dropna()
            
            if len(playtime_values) > 0:
                hours_list = [parse_playtime_to_hours(val) for val in playtime_values]
                hours_list = [h for h in hours_list if h > 0]
                
                if hours_list:
                    avg_hours = sum(hours_list) / len(hours_list)
                    row_data[week_col] = round(avg_hours, 2)
                else:
                    row_data[week_col] = 0.0
            else:
                row_data[week_col] = 0.0
        
        all_subbranch_data.append(row_data)
    
    if not all_subbranch_data:
        print("⚠️ No sub-branch data found.")
        return pd.DataFrame()
    
    result_df = pd.DataFrame(all_subbranch_data)
    
    stat_cols = ['SubBranch', 'Avg_KD_Ratio', 'Avg_HS_Percent', 'Avg_Kills', 'Avg_Deaths', 
                 'Avg_Level', 'Avg_Money', 'Avg_Damage', 'Avg_Headshots']
    week_cols_sorted = sorted([col for col in result_df.columns if ' - ' in str(col)])
    
    final_cols = stat_cols + week_cols_sorted
    result_df = result_df[[col for col in final_cols if col in result_df.columns]]
    
    print(f"✅ Created sub-branch pivots: {len(result_df)} sub-branches")
    
    return result_df


def _calculate_group_stats(data_df, group_name, week_columns):
    """(Unchanged logic)"""
    if data_df.empty:
        print(f"   ⚠️ No data for group: {group_name}")
        return None
    
    print(f"   Processing {len(data_df)} records for: {group_name}")
    row_data = {'Group': group_name}
    
    stats_columns = {
        'Avg_KD_Ratio': 'KD_Ratio',
        'Avg_HS_Percent': 'HS_Percent',
        'Avg_Kills': 'Kills',
        'Avg_Deaths': 'Deaths',
        'Avg_Level': 'Level',
        'Avg_Money': 'Money',
        'Avg_Damage': 'Damage',
        'Avg_Headshots': 'Headshots'
    }
    
    for stat_name, column_name in stats_columns.items():
        if column_name in data_df.columns:
            values = data_df[column_name].apply(safe_float)
            values = values[values > 0]
            row_data[stat_name] = round(values.mean(), 2) if len(values) > 0 else 0.0
        else:
            row_data[stat_name] = 0.0
    
    for week_col in week_columns:
        playtime_values = data_df[week_col].dropna()
        if len(playtime_values) > 0:
            hours_list = [parse_playtime_to_hours(val) for val in playtime_values]
            hours_list = [h for h in hours_list if h > 0]
            row_data[week_col] = round(sum(hours_list) / len(hours_list), 2) if hours_list else 0.0
        else:
            row_data[week_col] = 0.0
    
    return row_data


def calculate_us_pivots(pivot_df, roster_membership_df):
    """(Unchanged logic, uses config.SUB_BRANCH_MAPPING)"""
    print("\n[CALCULATING US & SOCOM PIVOT STATISTICS]")
    
    # Filter out outliers
    if 'Has_Outlier' in pivot_df.columns:
        clean_df = pivot_df[pivot_df['Has_Outlier'] == False].copy()
        outlier_count = len(pivot_df) - len(clean_df)
        if outlier_count > 0:
            print(f"   Excluding {outlier_count} player(s) with outliers from pivot")
    else:
        clean_df = pivot_df.copy()
    
    week_columns = [col for col in clean_df.columns if ' - ' in str(col)]
    
    # --- Group 1: US Military (All 4 main branches) ---
    main_branches = ['Army', 'USAF', 'USMC', 'NAVY']
    us_data = clean_df[clean_df['Branch'].isin(main_branches)].copy()
    
    # --- Group 2: US SOCOM (Any player in a sub-branch) ---
    sub_branch_cols = [f'Col_{i}_Member' for i in config.SUB_BRANCH_MAPPING.keys() if f'Col_{i}_Member' in roster_membership_df.columns]
    
    # Find SteamIDs of SOCOM members from the roster
    socom_mask = roster_membership_df[sub_branch_cols].any(axis=1)
    socom_steam_ids = roster_membership_df[socom_mask]['SteamID64'].unique()
    
    # Filter the clean data for those SteamIDs
    socom_data = clean_df[clean_df['SteamID64'].isin(socom_steam_ids)].copy()

    all_rows = []
    
    # Calculate US Military Stats
    us_row = _calculate_group_stats(us_data, "US Military", week_columns)
    if us_row:
        all_rows.append(us_row)
        
    # Calculate US SOCOM Stats
    socom_row = _calculate_group_stats(socom_data, "US SOCOM", week_columns)
    if socom_row:
        all_rows.append(socom_row)
    
    if not all_rows:
        print("⚠️ No data found for US or SOCOM groups.")
        return pd.DataFrame()

    # Create a DataFrame with 2 rows
    result_df = pd.DataFrame(all_rows)
    
    # Organize columns
    stat_cols = ['Group', 'Avg_KD_Ratio', 'Avg_HS_Percent', 'Avg_Kills', 'Avg_Deaths', 
                 'Avg_Level', 'Avg_Money', 'Avg_Damage', 'Avg_Headshots']
    week_cols_sorted = sorted([col for col in result_df.columns if ' - ' in str(col)])
    
    final_cols = stat_cols + week_cols_sorted
    result_df = result_df[[col for col in final_cols if col in result_df.columns]]
    
    print(f"✅ Created US pivots: {len(result_df)} rows (US & SOCOM)")
    
    return result_df

# --- MAIN ORCHESTRATOR ---

def scrape_and_merge_data():
    """(Main logic, uses config for paths, credentials, and settings)"""
    
    # Ensure output directory exists
    if not os.path.exists(config.OUTPUTS_DIR):
        os.makedirs(config.OUTPUTS_DIR)
    
    print("\n[STAGE 1/4: RESOLVING STEAM IDs AND FETCHING GMOD STATS]")
    
    try:
        steam_ids_list, roster_membership_df = get_steam_ids_from_google_sheet(
            config.CREDS_FILE_PATH, 
            config.SHEET_ID, 
            config.MASTER_SHEET_TAB_NAME, 
            max(config.STEAM_ID_COLUMN_INDEXES)
        )
    except Exception as e:
        print(f"Error reading from Google Sheet: {e}")
        return

    if not steam_ids_list:
        print("No Steam IDs found. Aborting.")
        return

    # Get Steam API Key from config
    steam_api_key = config.STEAM_API_KEY
    if not steam_api_key:
        print("❌ STEAM_API_KEY not found in .env file. Aborting.")
        return
    else:
        print("✅ Steam API Key loaded.")
    
    resolved_df = resolve_steam_ids_to_names(steam_ids_list, steam_api_key)
    
    if resolved_df.empty:
        print("No profiles resolved. Aborting.")
        return
    
    gmod_stats_df = fetch_gmod_leaderboard()
    
    if not gmod_stats_df.empty:
        print("\n[SAVING ICEFUSE LEADERBOARD]")
        gmod_stats_df.to_csv(config.LEADERBOARD_OUTPUT_FILENAME, index=False)
        print(f"✅ IceFuse leaderboard saved locally: {config.LEADERBOARD_OUTPUT_FILENAME}")
        
        upload_to_google_sheets(
            gmod_stats_df, 
            config.SHEET_ID, 
            config.LEADERBOARD_SHEET_TAB_NAME, 
            config.CREDS_FILE_PATH
        )
    
    roster_final_df = resolved_df.merge(roster_membership_df, on='SteamID64', how='left')
    
    if not gmod_stats_df.empty:
        print("\n[MERGING GMOD STATS WITH ROSTER]")
        roster_final_df = roster_final_df.merge(gmod_stats_df, on='SteamID64', how='left')
        stats_found = roster_final_df['Money'].notna().sum()
        print(f"✅ Merged GMod stats: {stats_found}/{len(roster_final_df)} players have stats")
    
    roster_final_df[['Branch', 'Sub_Branch']] = roster_final_df.apply(
        calculate_roster_fields, axis=1, result_type='expand'
    )
    
    identity_cols = ['SteamID64', 'Current_SteamName_from_API', 'ProfileStatus']
    
    if 'RP_Name' in roster_final_df.columns:
        identity_cols.append('RP_Name')
    
    identity_cols.extend(['Branch', 'Sub_Branch'])
    
    stats_cols = ['Player_Name', 'Money', 'Level', 'Total_Playtime', 'Kills', 'Deaths', 'KD_Ratio', 'Headshots', 'Damage', 'HS_Percent']
    for col in stats_cols:
        if col in roster_final_df.columns:
            identity_cols.append(col)
    
    roster_identity_df = roster_final_df[identity_cols].copy()

    print("\n[STAGE 2/4: SCRAPING BATTLEMETRICS DATA]")
    
    driver = None
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        historical_df = load_or_scrape_data(driver)

    except WebDriverException as e:
        print(f"WebDriver Error: {e}")
        return
    except Exception as e:
        print(f"Scraping Error: {e}")
        return
    finally:
        if driver:
            driver.quit()
    
    if historical_df.empty:
        print("Scrape yielded no data. Aborting.")
        return

    print("\n[STAGE 3/4: MERGING AND PIVOTING DATA]")
    
    merged_df = historical_df.merge(
        roster_identity_df, 
        left_on='BattleMetrics_Name', 
        right_on='Current_SteamName_from_API', 
        how='left'
    )

    merged_df['Week_Range'] = merged_df['Week_Start_UTC'] + ' - ' + merged_df['Week_End_UTC']
    
    pivot_index = identity_cols
    
    final_pivot_df = pd.pivot_table(
        merged_df, 
        index=pivot_index, 
        columns='Week_Range', 
        values='Time_Display', 
        aggfunc='first'
    ).reset_index()

    final_pivot_df = final_pivot_df.rename(columns={'Current_SteamName_from_API': 'SteamName_Current'})
    
    final_pivot_df = detect_and_warn_outliers(final_pivot_df)
    
    final_pivot_df.to_csv(config.FINAL_OUTPUT_FILENAME, index=False)
    print(f"✅ Main report saved: {config.FINAL_OUTPUT_FILENAME}")
    
    upload_to_google_sheets(
        final_pivot_df, 
        config.SHEET_ID, 
        config.OUTPUT_SHEET_TAB_NAME, 
        config.CREDS_FILE_PATH, 
        format_dates=True
    )
    
    print("\n[STAGE 4/4: CALCULATING PIVOTS]")
    
    branch_pivots_df = calculate_branch_pivots(final_pivot_df)
    
    if not branch_pivots_df.empty:
        branch_pivots_df.to_csv(config.BRANCH_PIVOT_OUTPUT_PATH, index=False)
        print(f"✅ Branch pivots saved: {config.BRANCH_PIVOT_OUTPUT_PATH}")
        
        upload_to_google_sheets(
            branch_pivots_df, 
            config.SHEET_ID, 
            config.BRANCH_PIVOT_SHEET_TAB_NAME, 
            config.CREDS_FILE_PATH, 
            format_dates=True
        )
    
    subbranch_pivots_df = calculate_subbranch_pivots(final_pivot_df, roster_membership_df)
    
    if not subbranch_pivots_df.empty:
        subbranch_pivots_df.to_csv(config.SUBBRANCH_PIVOT_OUTPUT_PATH, index=False)
        print(f"✅ Sub-branch pivots saved: {config.SUBBRANCH_PIVOT_OUTPUT_PATH}")
        
        upload_to_google_sheets(
            subbranch_pivots_df, 
            config.SHEET_ID, 
            config.SUBBRANCH_PIVOT_SHEET_TAB_NAME, 
            config.CREDS_FILE_PATH, 
            format_dates=True
        )
    
    us_pivots_df = calculate_us_pivots(final_pivot_df, roster_membership_df)
    
    if not us_pivots_df.empty:
        us_pivots_df.to_csv(config.US_PIVOT_OUTPUT_PATH, index=False)
        print(f"✅ US pivots saved: {config.US_PIVOT_OUTPUT_PATH}")
        
        upload_to_google_sheets(
            us_pivots_df, 
            config.SHEET_ID, 
            config.US_PIVOT_SHEET_TAB_NAME, 
            config.CREDS_FILE_PATH, 
            format_dates=True
        )

    print("\n" + "="*60)
    print(f"Pipeline Complete!")
    print(f"Total Players Tracked: {len(roster_identity_df)}")
    print(f"Reports Saved to: {config.OUTPUTS_DIR}")
    print("="*60)


if __name__ == "__main__":
    print("Running pipeline.py as a script...")
    scrape_and_merge_data()