import gspread
from google.oauth2.service_account import Credentials
import os
import sys
from pathlib import Path

# --- Add path to src to import config ---
# (scripts/ -> root -> src)
SRC_DIR = Path(__file__).parent.parent / 'src'
sys.path.append(str(SRC_DIR))

# --- Add root path to find .env file ---
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
os.chdir(ROOT_DIR) # Change working directory to root

try:
    # Try to import from the main config file
    from gmod_stat_tracker.config import SHEET_ID, MASTER_SHEET_TAB_NAME, CREDS_FILE_PATH
    print("✅ Successfully loaded from main config.")
except ImportError:
    print("❌ Could not import config. Using fallback constants...")
    SHEET_ID = '1xNcKf3IkfoEc4XgMdWoZ6-WJhNFG18y7yl9svitHy_0'
    MASTER_SHEET_TAB_NAME = 'RosterImports'
    # Path relative to scripts/ folder
    CREDS_FILE_PATH = '../google_sheets_service_account.json'
# ---

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDS_FILE_PATH, scopes=scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(SHEET_ID)
worksheet = spreadsheet.worksheet(MASTER_SHEET_TAB_NAME)

# Get first 10 rows
raw_data = worksheet.get_all_values()

print("First 10 rows from your sheet:")
print("="*60)
for i, row in enumerate(raw_data[:10], start=1):
    print(f"Row {i}: {row[:8]}")  # Show first 8 columns (A-H)
    
print("\n" + "="*60)
print(f"Total rows in sheet: {len(raw_data)}")
print(f"Total columns: {len(raw_data[0]) if raw_data else 0}")