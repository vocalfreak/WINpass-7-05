from PIL import Image, ImageOps
import face_recognition as fr
import cv2 
import numpy as np
import os 
import sqlite3
face_data_list = []

def resize_with_padding(img_path, size=(250, 250), fill_color=(0, 0, 0)):
    img = Image.open(img_path)
    img.thumbnail(size, Image.LANCZOS)
    delta_w = size[0] - img.size[0]
    delta_h = size[1] - img.size[1]
    padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)
    return ImageOps.expand(img, padding, fill=fill_color)

def get_face_encodings(img_path):
    img = cv2.imread(img_path)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_encoding = fr.face_encodings(rgb_img)
    return img_encoding

def collect_face_data(image_folder_path):
    for person in os.listdir(image_folder_path):
        person_folder = os.path.join(image_folder_path, person)
        if not os.path.isdir(person_folder):
            continue

        for image_name in os.listdir(person_folder):
            image_path = os.path.join(person_folder, image_name)
            try:
                encodings = get_face_encodings(image_path)
                for encoding in encodings:
                    face_data_list.append((person, encoding))
                    print(f"[+] Collected encoding for {person} - {image_name}")
            except Exception as e:
                print(f"[!] Failed to process {image_path} - {e}")
    
    print(f"\n Total encodings collected: {len(face_data_list)}")
    return face_data_list

def insert_face_data_to_db(face_data_list, db_path):
    conn = sqlite3.connect(db_path)
    print(f"Connected to {db_path}")
    cursor = conn.cursor()

    for name, encoding in face_data_list:
        try:
            encoded_blob = encoding.tobytes()

            cursor.execute('''
                INSERT INTO user (name, face_data)
                VALUES (?, ?)
            ''', (name, encoded_blob))

            print(f"[✓] Inserted: {name}")

        except Exception as e:
            print(f"[!] Failed to insert {name} - {e}")

    conn.commit()
    conn.close()
    print("\n All face data inserted into the database.")

collect_face_data(r"C:\Users\chiam\Downloads\winpass_training_set")
insert_face_data_to_db(face_data_list, r"C:\Users\chiam\Projects\WINpass-7-05\app\winpass.db")




