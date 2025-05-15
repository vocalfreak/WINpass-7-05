import json
import requests
import os
import csv
import pandas as pd
import subprocess as sp
from pathlib import Path 

def get_post_img(post_path):
    with open(post_path, 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)
    
    displayurl = df["displayUrl"]
    os.makedirs("posts_img", exist_ok=True)

    for idx, image_url in enumerate(displayurl.dropna()):
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            ext = image_url.split('.')[-1].split('?')[0]
            if len(ext) > 5 or '/' in ext:  
                ext = "jpg"
                file_path = os.path.join("posts_img", f"post_{idx}.{ext}")
                with open(file_path, "wb") as img_file:
                    img_file.write(response.content)

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

# PATH
post_path = r"C:\Users\chiam\Projects\WINpass-7-05\instagram_dataset.csv"
captions_path = r"C:\Users\chiam\Projects\WINpass-7-05\captions.csv"
posts_img_path = r"C:\Users\chiam\Projects\WINpass-7-05\posts_img"

#get_post_img(post_path)
#get_captions(post_path, captions_path)
get_tsv(posts_img_path)