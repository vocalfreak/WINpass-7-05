import json
import requests
import os
import csv
import pandas as pd
import subprocess as sp
import logging
from pathlib import Path 
import io
import sys
from apify_client import ApifyClient
import datetime
from utils.models_utils import logistic_regression, get_title_date, extract_event_data, get_events_data
import sqlite3
import time 
import schedule
import dateparser
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_instagram(csv_folder_path):

    client = ApifyClient("apify_api_fYSEzqJDmoUmbHEQ4FwHW30b8Ps2aa3LcE2D")

    run_input = {
  "resultsLimit": 2,
  "skipPinnedPosts": True,
  "username": [
    "itsocietymmu",
    "acsmmu",
    "buddhistsociety.mmu",
    "byic.mmu",
    "official_clsc_mmu",
    "commsocietymmu",
    "cmcmmu",
    "cac.mmu",
    "mmu.dice",
    "ebeevocals",
    "engsoc_mmucyb",
    "techgirls_mmu",
    "gdg.mmu",
    "iucyber ",
    "iss_mmucyber",
    "jcsmmu",
    "kcc_cyber",
    "mmucscyber",
    "fcammu",
    "radiommu",
    "gdcmmu",
    "ieeemmusb",
    "srcmmu_cyber",
    "mmusuperheroes",
    "rentakmmu",
    "srmcyber",
    "shsommu",
    "sccmmu_cyber",
    "tamucyb",
    "mmu.akido_club",
    "badmintonclubmmucyber",
    "mmucyberjayachessclub",
    "volbees_mmu",
    "mmucyberjayarchery",
    "mmusports",
    "mmuswimmingclub",
    "mmufccyber",
    "mmuwatersports",
    "netbeesmmu",
    "oarsmmucyber",
    "mmuhornbillsreds "
  ]
}

    run = client.actor("nH2AHrwxeTRJoN5hX").call(run_input=run_input)

    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    if not dataset_items:
        return None
    
    df = pd.DataFrame(dataset_items)

    time = datetime.now().strftime("%Y%m%d")
    csv_filename = f"instagram_posts_{time}.csv"

    csv_filepath = os.path.join(csv_folder_path, csv_filename)

    output_df = pd.DataFrame({
        "caption": df.get("caption", ""),
        "alt": df.get("alt", ""),
        "shortCode": df.get("shortCode", ""),
        "displayUrl": df.get("displayUrl", ""),
        "locationName": df.get("locationName", ""),
        "ownerFullName": df.get("ownerFullName", ""),
        "locationId": df.get("locationId", ""),
        "timestamp": df.get("timestamp", "")
    })
    
    output_df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
    return csv_filepath


def get_post_img(post_path):
    with open(post_path, 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)

    df = df[df["predicted"] == 1]  
    os.makedirs("posts_img", exist_ok=True)

    for image_url, post_id in zip(df["displayUrl"], df["shortCode"]):
        if pd.isna(image_url) or pd.isna(post_id):
            continue

        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                ext = image_url.split('.')[-1].split('?')[0]
                if len(ext) > 5 or '/' in ext:
                    ext = "jpg"
                file_path = os.path.join("static\posts_img", f"{post_id}.{ext}")
                with open(file_path, "wb") as img_file:
                    img_file.write(response.content)
        except Exception as e:
            print(f"Failed to download {post_id}: {e}")

def store_to_db(csv_filepath, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    existing_shortcodes = set()

    cursor.execute("SELECT shortCode FROM INSTAGRAM")
    results = cursor.fetchall()

    for result in results:
        existing_shortcodes.add(result[0])

    with open(csv_filepath, 'r', encoding='utf-8-sig') as f:
        df = pd.read_csv(f, dtype={'date': str})

    for index, row in df.iterrows():
        shortcode = row.get('shortCode')

        if shortcode in existing_shortcodes:
            continue 

        cursor.execute("""
        INSERT INTO instagram (caption, alt, shortCode, displayUrl, locationName, ownerFullName, locationId, timestamp, predicted, details, title, date, time, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['caption'],
            row['alt'],
            row['shortCode'],
            row['displayUrl'],
            row['locationName'],
            row['ownerFullName'],
            row['locationId'],
            row['timestamp'],
            row['predicted'],
            row['details'],
            row['title'],
            row['date'],
            row['time'],
            row['location'],
        ))

    conn.commit()
    conn.close()

def parse_date(post_path):
    df = pd.read_csv(post_path, encoding='utf-8-sig')
    dates = df["date"]

    parsedDates = []
    for date in dates:
        if pd.isna(date):
            parsedDates.append(None)
            continue 

        date = str(date).split('.')[0]
        dp = dateparser.parse(date)
        if dp:
            parsedDates.append(dp.strftime('%Y%m%d'))
        else:
            parsedDates.append(None)

    df["date"] = parsedDates 

    df.to_csv(post_path, index=False, encoding="utf-8-sig")

    
def data_pipeline(captions_training_path, csv_folder_path, db_path):
    csv_filepath = scrape_instagram(csv_folder_path) 

    logistic_regression(captions_training_path, csv_filepath)

    get_post_img(csv_filepath)

    get_title_date(csv_filepath)

    extract_event_data(csv_filepath)

    get_events_data(csv_filepath)

    parse_date(csv_filepath)

    store_to_db(csv_filepath, db_path)

def get_weekend_filter(today):
    saturday = today + timedelta((5 - today.weekday()) % 7)
    sunday = saturday + timedelta(days=1)
    return saturday, sunday

def get_tmr_filter(today):
    tmr = today + timedelta(days=1)
    return tmr 

def schedule_weekly_pipeline(captions_training_path, csv_folder_path, db_path):
    def run_scheduled_pipeline():
        data_pipeline(captions_training_path, csv_folder_path, db_path)
    
    schedule.every().monday.at("09:00").do(run_scheduled_pipeline)
    
    logger.info("Weekly pipeline scheduled for every Monday at 12:00 AM")
    

    while True:
        schedule.run_pending()
        time.sleep(3600)  
 

# PATH
# post_path = r"C:\Users\chiam\Projects\WINpass-7-05\weekly_scrapes_csv\instagram_posts.csv"
# captions_training_path = r"C:\Users\chiam\Projects\WINpass-7-05\captions_trainingset.csv"
# # posts_img_path = r"C:\Users\chiam\Projects\WINpass-7-05\posts_img"
# csv_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\weekly_scrapes_csv"
# db_path = "winpass.db"


posts_img_path = "posts_img"

post_path = "weekly_scrapes_csv\instagram_posts_20250609.csv"
captions_training_path = "captions_trainingset.csv"
csv_folder_path = "weekly_scrapes_csv"
db_path = "winpass.db"
