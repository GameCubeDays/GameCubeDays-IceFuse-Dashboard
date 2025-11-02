import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
from datetime import datetime, timedelta 
import urllib.parse 
from typing import List, Dict, Any

# Import configuration (Absolute Import)
from gmod_stat_tracker import config


def generate_leaderboard_url(base_url: str, start_date: datetime, end_date: datetime) -> str:
    """Generates the BattleMetrics leaderboard URL for a specific time period."""
    start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    period_value = f"{start_iso}:{end_iso}"
    
    query_params = {"filter[period]": period_value}
    encoded_params = urllib.parse.urlencode(query_params, safe='[]:')
    final_url = f"{base_url}?{encoded_params}"
    return final_url


def login_to_battlemetrics(driver: webdriver.Chrome, username: str, password: str) -> bool:
    """Navigates to the login page and submits credentials."""
    LOGIN_URL = "https://www.battlemetrics.com/account/login"
    driver.get(LOGIN_URL)
    
    try:
        username_field = WebDriverWait(driver, 5).until( 
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        username_field.send_keys(username) 
        password_field.send_keys(password)
        login_button.click()

        try:
            WebDriverWait(driver, 10).until(EC.url_changes(LOGIN_URL))
            WebDriverWait(driver, 3).until( 
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/account']"))
            )
            print("✅ Login successful")
            return True
        except TimeoutException:
            try:
                driver.find_element(By.CLASS_NAME, "alert-danger")
                print("❌ Login failed: Credentials rejected.")
                return False
            except NoSuchElementException:
                print("❌ Login failed: Timed out waiting for redirect or post-login element.")
                return False

    except Exception as e:
        print(f"❌ Login Error: Could not find login fields/button: {e}")
        return False


def scrape_leaderboard_page(driver: webdriver.Chrome, page_number: int) -> List[Dict[str, Any]]:
    """(Unchanged logic)"""
    data: List[Dict[str, Any]] = []
    TABLE_CSS_SELECTOR = "table" 
    
    try:
        WebDriverWait(driver, 10).until( 
            EC.presence_of_element_located((By.CSS_SELECTOR, TABLE_CSS_SELECTOR)) 
        )
        
        row_elements = driver.find_elements(By.CSS_SELECTOR, f"{TABLE_CSS_SELECTOR} tbody tr")

        for row in row_elements:
            try:
                rank_element = row.find_element(By.TAG_NAME, "td")
                player_name_element = row.find_element(By.CSS_SELECTOR, "td.player a")
                time_element = row.find_element(By.TAG_NAME, "time")
                
                rank = rank_element.text.strip()
                player_name = player_name_element.text.strip()
                score_display = time_element.text.strip()
                score_iso = time_element.get_attribute("datetime") 

                data.append({
                    "Rank": rank,
                    "BattleMetrics_Name": player_name, 
                    "Time_Display": score_display,
                    "Time_ISO_Duration": score_iso
                })
            except (NoSuchElementException, StaleElementReferenceException):
                continue

    except TimeoutException:
        print("   ❌ Error: Table failed to load or CSS selector is wrong.")
    except Exception as e:
        print(f"   ❌ Scraping Error on Page {page_number}: {e}")
        
    return data


def scrape_all_pages(driver: webdriver.Chrome, start_url: str) -> pd.DataFrame:
    """(Unchanged logic)"""
    driver.get(start_url)
    time.sleep(2) 
    
    all_data = []
    page_number = 1
    
    while True:
        print(f"   Scraping Page {page_number}...")
        
        current_page_data = scrape_leaderboard_page(driver, page_number)
        all_data.extend(current_page_data)
        
        next_button_selector = "a[href*='page%5Brel%5D=next']" 
        
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector))
            )
            
            next_button.click()
            page_number += 1
            time.sleep(1)
            
        except TimeoutException:
            print(f"   ✅ Finished: Scraped {page_number} page(s). 'Next' button not found.")
            break
        except Exception as e:
            print(f"   ❌ Pagination Error: {e}. Exiting loop.")
            break
            
    return pd.DataFrame(all_data)


def scrape_multiple_weeks(driver: webdriver.Chrome, base_url: str, weeks_to_scrape: int) -> pd.DataFrame:
    """(Unchanged logic)"""
    all_data_frames: List[pd.DataFrame] = []
    
    current_end = datetime.utcnow().replace(hour = 4, minute=0, second=0, microsecond=0)
    WEEK = timedelta(days=7) 
    
    for week_offset in range(weeks_to_scrape):
        end_date = current_end - (WEEK * week_offset)
        start_date = end_date - WEEK
        
        print(f"\n--- WEEK {week_offset + 1} of {weeks_to_scrape}: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')} (UTC) ---")
        
        current_url = generate_leaderboard_url(base_url, start_date, end_date)
        weekly_df = scrape_all_pages(driver, current_url)
        
        if not weekly_df.empty:
            weekly_df['Week_Start_UTC'] = start_date.strftime('%Y-%m-%d %H:%M')
            weekly_df['Week_End_UTC'] = end_date.strftime('%Y-%m-%d %H:%M')
            all_data_frames.append(weekly_df)
            print(f"✅ Data retrieved successfully for Week {week_offset + 1}: {len(weekly_df)} records")
        else:
            print(f"❌ Warning: Retrieved no data for Week {week_offset + 1}. Skipping.")

    if all_data_frames:
        final_df = pd.concat(all_data_frames, ignore_index=True)
        print(f"\n✅ Total records scraped across all weeks: {len(final_df)}")
        return final_df
    else:
        print("\n❌ No data scraped from any week.")
        return pd.DataFrame()