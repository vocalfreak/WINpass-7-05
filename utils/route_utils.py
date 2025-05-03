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
                INSERT INTO user (mmu_id, name, password, career, faculty, campus, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['mmu_id'],
                    row['name'],
                    row['career'],
                    row['password'],
                    row['faculty'],
                    row['campus'],
                    row['email'],
           ))
        
        conn.commit()

    except Exception as e:
         print(f"Error importing csv: {e}")

    conn.close()

def get_conection():
    conn = sqlite3.connect('winpass.db')
    conn.row_factory = sqlite3.Row 
    return conn

def photobooth():
    
    folder_name = "pictures"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    cam = cv2.VideoCapture(0)

    cv2.namedWindow("Photobooth")

    img_counter = 0

    while True:
        ret,frame = cam.read()

        if not ret:
            print("Failed to grab the frame")
            break

        cv2.imshow("Photobooth",frame)

        k=cv2.waitKey(1)

        if k%256 == 27:
            print("Escape hit, closing the app")
            break
        
        elif k%256 == 32:
            img_name = os.path.join(folder_name,"opencv_frame_{}.png".format(img_counter))
            cv2.imwrite(img_name,frame)
            print("Photo taken")
            img_counter+=1

    cam.release()
    cv2.destroyAllWindows()



                

                
