import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- PROJECT ROOT ---
# (src/gmod_stat_tracker/config.py -> src/ -> root)
BASE_DIR = Path(__file__).parent.parent.parent

# --- OUTPUT DIRECTORIES ---
OUTPUTS_DIR = BASE_DIR / 'outputs'
GRAPHS_DIR = BASE_DIR / 'graphs'
CACHE_DIR = BASE_DIR / 'cache'

# --- CREDENTIALS & SECRETS ---
BATTLEMETRICS_USERNAME = os.getenv("BATTLEMETRICS_USERNAME")
BATTLEMETRICS_PASSWORD = os.getenv("BATTLEMETRICS_PASSWORD")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# --- FILE PATHS ---
CREDS_FILE_PATH = BASE_DIR / 'google_sheets_service_account.json'
CACHE_FILENAME = CACHE_DIR / 'historical_data_cache.pkl'

# Output CSV files
FINAL_OUTPUT_FILENAME = OUTPUTS_DIR / 'consolidated_playtime_report.csv'
BRANCH_PIVOT_OUTPUT_PATH = OUTPUTS_DIR / 'branch_pivots.csv'
SUBBRANCH_PIVOT_OUTPUT_PATH = OUTPUTS_DIR / 'subbranch_pivots.csv'
US_PIVOT_OUTPUT_PATH = OUTPUTS_DIR / 'us_pivots.csv'
LEADERBOARD_OUTPUT_FILENAME = OUTPUTS_DIR / 'icefuse_leaderboard.csv'

# --- BATTLEMETRICS ---
BASE_LEADERBOARD_URL = "https://www.battlemetrics.com/servers/gmod/28685000/leaderboard"
WEEKS_TO_PULL = 8
CACHE_EXPIRY_HOURS = 1

# --- GMOD API ---
GMOD_API_URL = "https://icefuse.net/api/gmod_leaderboards"
SERVER_ID = 23
MAX_RESULTS = 5000

# --- GOOGLE SHEETS ---
SHEET_ID = '1xNcKf3IkfoEc4XgMdWoZ6-WJhNFG18y7yl9svitHy_0'
MASTER_SHEET_TAB_NAME = 'RosterImports'

# Output Tabs
OUTPUT_SHEET_TAB_NAME = 'Player_Report'
BRANCH_PIVOT_SHEET_TAB_NAME = 'BranchPivots'
SUBBRANCH_PIVOT_SHEET_TAB_NAME = 'SubBranchPivots'
US_PIVOT_SHEET_TAB_NAME = 'USPivots'
LEADERBOARD_SHEET_TAB_NAME = 'IceFuse_Leaderboard'

# --- ROSTER MAPPINGS ---
STEAM_ID_COLUMN_INDEXES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

BRANCH_MAPPING = {
    1: "Army",
    2: "USAF",
    3: "USMC",
    4: "NAVY",
    5: "Unknown",
    6: "Unknown",
    7: "Unknown",
    8: "Unknown",
    9: "Unknown",
    10: "Unknown",
    11: "Unknown",
}

SUB_BRANCH_MAPPING = {
    5: "75th",
    6: "89th",
    7: "FORECON",
    8: "MARSOC",
    9: "SEALS",
    10: "DEVGRU",
    11: "DELTA",
}