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
    ds["timestamp"] = df["timestamp"]
    
    ds.to_csv(csv_filepath, index=False)


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

def get_captions(post_path, captions_path):
    with open(post_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    captions = []
    for post in data:
        caption = post.get('caption') or post.get("edge_media_to_caption", {}).get("edges", [{}][0].get("node", {}).get("texxt"))
        if caption:
            captions.append({
                "caption": caption,
            })
    with open(captions_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["caption"])  
        writer.writerows(captions)

def get_tsv(images_dir):
    images_dir = Path(images_dir)
    for image_file in images_dir.glob("*.jpg"):
        output_path = image_file.with_suffix('')  
        cmd = [
            "tesseract",  
            str(image_file),
            str(output_path),
            "--oem", "3",
            "--psm", "11",
            "tsv"
        ]
        print("Running command:", " ".join(cmd))  
        sp.run(cmd, check=True) 

def get_events_title(post_path):
    df = pd.read_csv(post_path, encoding='utf-8-sig')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    titles = []
    for _, row in df.iterrows():
        if row['predicted'] == 1:
            caption = row.get('caption', '')
            lines = [line.strip() for line in caption.split('\n') if line.strip()]
            if lines:
                titles.append(lines[0])
            else:
                titles.append('')
        else:
            titles.append(None)

    df["title"] = titles
    df.to_csv(post_path, index=False, encoding='utf-8-sig')

def data_pipeline(instagram_posts_path):
    pass

# PATH
post_path = r"C:\Users\chiam\Projects\WINpass-7-05\instagram_posts.csv"
captions_training_path = r"C:\Users\chiam\Projects\WINpass-7-05\captions_trainingset.csv"
posts_img_path = r"C:\Users\chiam\Projects\WINpass-7-05\posts_img"


#get_events_title(post_path)
#get_post_img(post_path)