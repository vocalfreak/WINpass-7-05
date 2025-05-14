import json
import requests
import os

def get_post_img(post_path):
    with open(post_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs("posts_img", exist_ok=True)

    for i, post in enumerate(data):
        url = post.get('displayUrl') 
        if url:
            try:
                img_data = requests.get(url).content
                with open(f"posts_img/img_{i}.jpg", 'wb') as handler:
                    handler.write(img_data)
                print(f"Downloaded image {i}")
            except Exception as e:
                print(f"Could not find image {i}: {e}")
        else:
            print(f"Could not find URL: {i}")

# Set your path here
post_path = r"C:\Users\chiam\Projects\WINpass-7-05\dataset_instagram-post-scraper_2025-05-07_08-55-02-774.json"

get_post_img(post_path)
