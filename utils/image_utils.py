import os
from PIL import Image, ImageOps
import sqlite3
import numpy as np
import cv2 
import qrcode
import requests
from flask import current_app
from urllib.parse import urlparse
import base64
import mimetypes


def generate_qr(mmu_id, data):
    qr = qrcode.make(data).resize((160, 160))
    qr_folder = os.path.join(current_app.root_path, 'static', 'qr_codes')
    os.makedirs(qr_folder, exist_ok=True)

    qr_path = os.path.join(qr_folder, f'{mmu_id}.png')
    qr.save(qr_path)

    return f'qrcodes/{mmu_id}.png'

        
def generate_winpass(name, mmu_id, db_path, image_folder_path):
    person_folder_path = os.path.join(image_folder_path, name.replace(' ', '_'))
    if os.path.exists(person_folder_path):
        image_files = [f for f in os.listdir(person_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:1]
        
        for i, img_file in enumerate(image_files):
            img_path = os.path.join(person_folder_path, img_file)
            try:
                img = cv2.imread(img_path)
                if img is not None:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    cursor.execute("SELECT hall, career FROM user WHERE mmu_id = ?", (mmu_id,))
                    hall, career = cursor.fetchone()
                    conn.close()

                    generate_qr(mmu_id, f"http://127.0.0.1:5000/{mmu_id}")
                    qr_path = f"qr_codes/{mmu_id}.png"

                    return name, mmu_id, hall, career, img_path, qr_path
                
            except Exception as e:
                print(f"Error displaying image {img_path}: {e}")

def get_winpass_info(mmu_id, db_path, image_folder_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name, hall, career FROM user WHERE mmu_id = ?", (mmu_id,))
    name, hall, career = cursor.fetchone()
    conn.close()

    person_folder_path = os.path.join(image_folder_path, name.replace(' ', '_'))
    if os.path.exists(person_folder_path):
        image_files = [f for f in os.listdir(person_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][:1]

        for i, img_file in enumerate(image_files):
            img_path = os.path.join(person_folder_path, img_file)
    
    return name, mmu_id, hall, career, img_path
    
def get_face_encodings_batch(image_folder_path, db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_encodings = 0
    
    for person_folder in os.listdir(image_folder_path):
        folder_path = os.path.join(image_folder_path, person_folder)
        if not os.path.isdir(folder_path):
            continue
        
        person_name = person_folder.replace('_', ' ')
        
        all_encodings = []
        
        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)
            try:
                img = cv2.imread(image_path)
                if img is None:
                    print(f"Could not read image: {image_path}")
                    continue

                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encodings = fr.face_encodings(rgb_img)
                
                if encodings:
                    for encoding in encodings:
                        all_encodings.append(encoding)
                        total_encodings += 1
                        print(f"[+] Collected encoding for {person_name} - {image_name}")
                else:
                    print(f"[-] No face found in {person_name} - {image_name}")
                    
            except Exception as e:
                print(f"Error processing {person_name} - {image_name}: {e}")
        
        if all_encodings:

            all_encodings_array = np.array(all_encodings)
            encodings_blob = all_encodings_array.tobytes()

            cursor.execute("SELECT id FROM user WHERE name = ?", (person_name,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                cursor.execute("UPDATE user SET face_data = ? WHERE id = ?", 
                              (encodings_blob, existing_user[0]))
                print(f"Updated face data for {person_name} with {len(all_encodings)} encodings")
            else:
                cursor.execute('''
                INSERT INTO user (name, face_data)
                VALUES (?, ?)
                ''', (person_name, encodings_blob))
                print(f"Added new user {person_name} with {len(all_encodings)} encodings")
                      
    conn.commit()
    conn.close()
    print(f"\nTotal encodings collected and stored: {total_encodings}")



def get_face_encodings_folders(image_folder_path):
    face_encodings = []

    for image_name in sorted(os.listdir(image_folder_path)):
        image_path = os.path.join(image_folder_path, image_name)
        try:
            img = cv2.imread(image_path)
            if img is None:
                print(f"Could not read image: {image_path}")
                continue

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = fr.face_encodings(rgb_img)

            if encodings:
                face_encodings.append(encodings[0])
                print(f"[+] Found encoding for {image_name}")
            else:
                print(f"[-] No face found in {image_name}")

        except Exception as e:
            print(f"Error processing {image_name}: {e}")

    valid_encodings = [encoding for encoding in face_encodings if encoding is not None]
    
    if len(valid_encodings) < 2:
        return None

    combined_encoding = np.mean(valid_encodings, axis=0)
    
    return combined_encoding


def get_decode_face_data(db_path):
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT mmu_id, name, face_data FROM user WHERE face_data IS NOT NULL")
    users = cursor.fetchall()
    conn.close()

    known_face_encodings = []
    known_face_names = []
    known_mmu_ids = []

    for mmu_id, name, face_data_blob in users:
        if face_data_blob:
            encodings_array = np.frombuffer(face_data_blob, dtype=np.float64)
            stored_encodings = encodings_array.reshape(-1, 128)

            for encoding in stored_encodings:
                known_face_encodings.append(encoding)
                known_face_names.append(name)
                known_mmu_ids.append(mmu_id)

    print(f"Loaded {len(known_face_encodings)} face encodings from {len(users)} users")
    return known_face_encodings, known_face_names, known_mmu_ids

def goodies_qr( db_path):
    print(f"Using database path: {db_path}")
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
    
        data, bbox, _ = detector.detectAndDecode(frame)

        if bbox is not None:
            points = bbox.astype(int)
            frame = cv2.polylines(frame, [points], isClosed=True, color=(0, 255, 0), thickness=3)

            if data:
                frame = cv2.putText(frame, data, (points[0][0][0], points[0][0][1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                print(f"QR Code Detected: {data}")

                parsed = urlparse(data.strip())
                mmu_id = parsed.path.lstrip('/')
                print(f"Parsed data: {parsed}")
                print(f"QR Code Detected: {mmu_id}")

                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE user SET goodies_status = ? WHERE mmu_id = ?", ('collected', mmu_id))
                    conn.commit()
                    conn.close()
                    
                    print(f"Updated database for MMU ID: {mmu_id}")
                    break
                except Exception as e:
                    print("Failed to connect to server:", e)

        cv2.imshow("QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return mmu_id



def badge_qr( db_path):
    print(f"Using database path: {db_path}")
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
    
        data, bbox, _ = detector.detectAndDecode(frame)

        if bbox is not None:
            points = bbox.astype(int)
            frame = cv2.polylines(frame, [points], isClosed=True, color=(0, 255, 0), thickness=3)

            if data:
                frame = cv2.putText(frame, data, (points[0][0][0], points[0][0][1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                print(f"QR Code Detected: {data}")

                parsed = urlparse(data.strip())
                mmu_id = parsed.path.lstrip('/')
                print(f"Parsed data: {parsed}")
                print(f"QR Code Detected: {mmu_id}")

                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    print(f"Executing query: UPDATE user SET badge_status = 'collected' WHERE mmu_id = {mmu_id}")
                    cursor.execute("UPDATE user SET badge_status = ? WHERE mmu_id = ?", ('collected', mmu_id))
                    conn.commit()
                    conn.close()
                    
                    print(f"Updated database for MMU ID: {mmu_id}")
                    break
                except Exception as e:
                    print("Failed to connect to server:", e)

        cv2.imshow("QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = 'image/png'  
            
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{img_data}"

# Paths
dataset_path = "winpass_training_set"
database_path = "winpass.db"
image_folder_path = "winpass_training_set"

#database_path = r"C:\Mini IT\WINpass-7-05\winpass.db"
#db_path = r"C:\Mini IT\WINpass-7-05\winpass.db"
#image_folder_path = r"C:\Mini IT\WINpass-7-05\winpass_training_set"


db_path = database_path 

#get_face_encodings_batch(image_folder_path, db_path)







