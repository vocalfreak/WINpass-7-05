import os
from PIL import Image, ImageOps
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
                INSERT INTO user (name, password, mmu_id, email, career, faculty, campus)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['name'],
                    row['password'],
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

def get_conection():
    conn = sqlite3.connect('winpass.db')
    conn.row_factory = sqlite3.Row 
    return conn



                

                
