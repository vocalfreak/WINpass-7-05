import os
from PIL import Image, ImageOps
import face_recognition as fr
import sqlite3
import numpy as np
import cv2 
import csv

def import_csv_init(df_path, db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        with open(df_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                cursor.execute("""
                INSERT INTO user (name, mmu_id, email, career, faculty, campus)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row['name'],
                    row['mmu_id'],
                    row['email'],
                    row['career'],
                    row['faculty'],
                    row['campus']
                    
           ))
        
        conn.commit()

    except Exception as e:
         print(f"Error importing csv: {e}")

    conn.close()

# Paths
df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"


import_csv_init(df_path, db_path)


                

                
