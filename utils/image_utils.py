import os
import cv2
import face_recognition as fr
import sqlite3
import numpy as np

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
        pass
    
    conn.commit()
    conn.close()
    print(f"\nTotal encodings collected and stored: {total_encodings}")

# Paths
dataset_path = r"C:\Users\chiam\Downloads\winpass_training_set"
database_path = r"C:\Users\chiam\Projects\WINpass-7-05\app\winpass.db"

