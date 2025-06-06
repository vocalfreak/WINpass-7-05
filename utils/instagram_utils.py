import json
import requests
import os
import csv
import pandas as pd
import subprocess as sp
from pathlib import Path 
import io
import sys
from apify_client import ApifyClient
import datetime
from models_utils import logistic_regression, get_title_date, extract_event_data, get_events_data
import sqlite3
import dateparser 

def scrape_instagram(csv_folder_path):

    client = ApifyClient("apify_api_fYSEzqJDmoUmbHEQ4FwHW30b8Ps2aa3LcE2D")

    run_input = {
  "resultsLimit": 2,
  "skipPinnedPosts": true,
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
    df = pd.DataFrame(dataset_items)

    time = datetime.now().strftime("%Y%m%d")
    csv_filename = f"instagram_posts_{time}.csv"

    csv_filepath = os.path.join(csv_folder_path, csv_filename)
    with open(csv_filepath, 'w', encoding='utf-8-sig') as f:
        ds = pd.read_csv(f)

    ds["caption"] = df["caption"]
    ds["alt"] = df["alt"]
    ds["shortCode"] = df["shortCode"]
    ds["displayUrl"] = df["displayUrl"]
    ds["locationName"] = df["locationName"]
    ds["ownerFullName"] = df["ownerFullName"]
    ds["locationId"] = df["locationId"]
    ds["timestamp"] = df["timestamp"]
    
    ds.to_csv(csv_filepath, index=False)
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
                file_path = os.path.join("posts_img", f"{post_id}.{ext}")
                with open(file_path, "wb") as img_file:
                    img_file.write(response.content)
        except Exception as e:
            print(f"Failed to download {post_id}: {e}")


def store_to_db(post_path, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(post_path, 'r', encoding='utf-8-sig') as f:
        df = csv.DictReader(f)

        for row in df:
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
        date = str(date)
        dp = dateparser.parse(date)
        if dp:
            parsedDates.append(dp.strftime('%Y%m%d'))
        else:
            dp.append(None)

    df["date"] = parsedDates 

    df.to_csv(post_path, index=False, encoding="utf-8-sig")

    
def data_pipeline():
    csv_filepath = scrape_instagram(csv_folder_path) 

    logistic_regression(csv_filepath, captions_training_path)

    get_post_img(csv_filepath)

    get_title_date(csv_filepath)

    extract_event_data(csv_filepath)

    get_events_data(csv_filepath)

    store_to_db(csv_filepath, db_path)




# PATH
post_path = r"C:\Users\chiam\Projects\WINpass-7-05\weekly_scrapes_csv\instagram_posts.csv"
captions_training_path = r"C:\Users\chiam\Projects\WINpass-7-05\captions_trainingset.csv"
# posts_img_path = r"C:\Users\chiam\Projects\WINpass-7-05\posts_img"
csv_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\weekly_scrapes_csv"
db_path = "winpass.db"


posts_img_path = r"C:\Mini IT\WINpass-7-05\static\posts_img"