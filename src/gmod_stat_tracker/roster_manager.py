import pandas as pd
import requests
import gspread
import sys
from google.oauth2.service_account import Credentials
import os
from typing import List, Dict, Any, Tuple

# Import configuration (Absolute Import)
from gmod_stat_tracker import config

def get_steam_ids_from_google_sheet(creds_file_path, sheet_id, tab_name, max_columns):
    """(Unchanged logic)"""
    roster_data = {}
    print("Connecting to Google Sheets...")
    
    if not os.path.exists(creds_file_path):
        print(f"Credentials file not found at {creds_file_path}")
        return [], pd.DataFrame()

    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(creds_file_path, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(tab_name)
        print(f"Connected to worksheet: {tab_name}")
        
    except Exception as e:
        print(f"Connection Error: {e}")
        return [], pd.DataFrame()

    try:
        raw_data = worksheet.get_all_values()
        
        if not raw_data or len(raw_data) < 2:
            print("Worksheet is empty.")
            return [], pd.DataFrame()
        
        data_rows = raw_data[1:]
        print(f"Found {len(data_rows)} rows")

        all_steam_ids = set()
        
        for row in data_rows:
            for col_index in range(min(len(row), max_columns)):
                raw_value = str(row[col_index]).strip()
                
                if len(raw_value) == 17 and raw_value.isdigit():
                    steam_id = raw_value
                    all_steam_ids.add(steam_id)

                    if steam_id not in roster_data:
                        roster_data[steam_id] = {'SteamID64': steam_id}
                        for i in range(1, max_columns + 1):
                            roster_data[steam_id][f'Col_{i}_Member'] = False

                    roster_data[steam_id][f'Col_{col_index + 1}_Member'] = True

        print(f"Found {len(all_steam_ids)} unique Steam IDs")
        
        roster_membership_df = pd.DataFrame(roster_data.values())
        return list(all_steam_ids), roster_membership_df

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return [], pd.DataFrame()


def resolve_steam_ids_to_names(steam_ids, api_key):
    """(Unchanged logic)"""
    if not steam_ids:
        return pd.DataFrame()

    print(f"Resolving {len(steam_ids)} Steam IDs...")
    
    MAX_IDS_PER_REQUEST = 100
    resolved_players = []

    for i in range(0, len(steam_ids), MAX_IDS_PER_REQUEST):
        batch = steam_ids[i:i + MAX_IDS_PER_REQUEST]
        steamids_str = ",".join(batch)
        
        API_URL = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steamids_str}"
        
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['response']['players']:
                for player in data['response']['players']:
                    resolved_players.append({
                        "SteamID64": player.get('steamid'),
                        "Current_SteamName_from_API": player.get('personaname'),
                        "ProfileStatus": "Public" if player.get('communityvisibilitystate') == 3 else "Friends Only/Private"
                    })

        except Exception as e:
            print(f"API Error: {e}")
        
    print(f"Resolved {len(resolved_players)} profiles")
    return pd.DataFrame(resolved_players)


if __name__ == "__main__":
    # This block needs to import config to run standalone
    try:
        from gmod_stat_tracker import config
    except ImportError:
        # Fallback if run directly and src is not in path
        import config
        
    print("Testing Roster Manager...")
    
    test_api_key = config.STEAM_API_KEY
    if not test_api_key:
        test_api_key = input("Enter Steam API Key (not found in config): ").strip()

    ids, roster_df = get_steam_ids_from_google_sheet(
        config.CREDS_FILE_PATH, 
        config.SHEET_ID, 
        config.MASTER_SHEET_TAB_NAME, 
        max(config.STEAM_ID_COLUMN_INDEXES)
    )

    if ids:
        print(f"\nSuccess! Found {len(ids)} Steam IDs")
        print("\nFirst 5 entries:")
        print(roster_df.head())
        
        if test_api_key:
            resolved_df = resolve_steam_ids_to_names(ids, test_api_key)
            if not resolved_df.empty:
                print(f"\nResolved profiles:")
                print(resolved_df.head())
    else:
        print("No Steam IDs found")