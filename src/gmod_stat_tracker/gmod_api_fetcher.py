import requests
import pandas as pd
from typing import Dict, List
import re

# Import configuration (Absolute Import)
from gmod_stat_tracker import config

def clean_html(text):
    """(Unchanged logic)"""
    if text is None or text == '':
        return ''
    text = str(text)
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()


def fetch_gmod_leaderboard():
    """
    Fetches the entire GMod leaderboard from Icefuse API.
    Returns a DataFrame with player statistics.
    (Uses config variables)
    """
    print("\n[FETCHING GMOD LEADERBOARD DATA]")
    
    params = {
        'server_id': config.SERVER_ID,
        'draw': 1,
        'start': 0,
        'length': config.MAX_RESULTS,
        'search[value]': '',
        'order[0][dir]': 'desc',
        'orderBy': 'money',
        'category': 'all'
    }
    
    try:
        print(f"Requesting data from Icefuse API...")
        response = requests.get(config.GMOD_API_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' not in data or not isinstance(data['data'], list):
            print("❌ API response missing 'data' array")
            return pd.DataFrame()
        
        leaderboard_data = data['data']
        
        if len(leaderboard_data) == 0:
            print("⚠️ API returned empty data array")
            return pd.DataFrame()
        
        print(f"✅ Fetched {len(leaderboard_data)} leaderboard entries")
        
        parsed_data = []
        
        for row in leaderboard_data:
            if 'steamid' in row and row['steamid']:
                parsed_row = {
                    'SteamID64': clean_html(row.get('steamid', '')),
                    'Rank': clean_html(row.get('pos', '')),
                    'RP_Name': clean_html(row.get('rpname', '')),
                    'Player_Name': clean_html(row.get('name', '')),
                    'Money': clean_html(row.get('money', '')),
                    'Level': clean_html(row.get('level', '')),
                    'Total_Playtime': clean_html(row.get('playtime', '')),
                    'Kills': clean_html(row.get('kills', '')),
                    'Deaths': clean_html(row.get('deaths', '')),
                    'KD_Ratio': clean_html(row.get('kd_ratio', '')),
                    'Headshots': clean_html(row.get('headshots', '')),
                    'Damage': clean_html(row.get('damage', '')),
                    'HS_Percent': clean_html(row.get('headshot_percent', ''))
                }
                parsed_data.append(parsed_row)
        
        df = pd.DataFrame(parsed_data)
        
        print(f"✅ Parsed {len(df)} player records")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error parsing leaderboard data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


if __name__ == "__main__":
    print("="*60)
    print("Testing GMod Stats Fetcher")
    print("="*60)
    
    df = fetch_gmod_leaderboard()
    
    if not df.empty:
        print("\n" + "="*60)
        print("SUCCESS! First 5 entries:")
        print("="*60)
        print(df.head().to_string(index=False))
        
        df.to_csv('gmod_leaderboard_test.csv', index=False)
        print(f"\n✅ Full data saved to: gmod_leaderboard_test.csv")
        print(f"   Total records: {len(df)}")
    else:
        print("\n❌ Failed to fetch data")