import os
from PIL import Image, ImageOps
import face_recognition as fr
import sqlite3
import numpy as np

def resize_image(img_path, size=(250, 250), fill_color=(0, 0, 0)):
    img = Image.open(img_path)
    img.thumbnail(size, Image.LANCZOS)
    delta_w = size[0] - img.size[0]
    delta_h = size[1] - img.size[1]
    padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)
    return ImageOps.expand(img, padding, fill=fill_color)

def get_face_encodings(image_folder_path, db_path):
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_encodings = 0
    
    for person_folder in os.listdir(image_folder_path):
        folder_path = os.path.join(image_folder_path, person_folder)
        if not os.path.isdir(folder_path):
            continue
        
        person_name = person_folder.replace('_', ' ')
        
        all_encodings = []
        continue 
    
    conn.commit()
    conn.close()
    print(f"\nTotal encodings collected and stored: {total_encodings}")

def 

# Paths
dataset_path = r"C:\Users\chiam\Downloads\winpass_training_set"
database_path = r"C:\Users\chiam\Projects\WINpass-7-05\app\winpass.db"

