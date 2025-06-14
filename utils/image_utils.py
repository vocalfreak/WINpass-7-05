import os
from PIL import Image, ImageOps
import face_recognition as fr
import sqlite3
import numpy as np
import cv2 
import qrcode
import requests
from flask import current_app
from urllib.parse import urlparse
import base64
import mimetypes

def resize_image(img_path, size=(250, 250), fill_color=(0, 0, 0)):

    img = Image.open(img_path)
    img.thumbnail(size, Image.LANCZOS)
    delta_w = size[0] - img.size[0]
    delta_h = size[1] - img.size[1]
    padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)
    return ImageOps.expand(img, padding, fill=fill_color)

def generate_qr(mmu_id, data):
    qr = qrcode.make(data).resize((160, 160))
    qr_folder = os.path.join(current_app.root_path, 'static', 'qr_codes')
    os.makedirs(qr_folder, exist_ok=True)

    qr_path = os.path.join(qr_folder, f'{mmu_id}.png')
    qr.save(qr_path)

    return f'qrcodes/{mmu_id}.png'

def check_ticket_status(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT ticket_status FROM user")
        ticket_status = cursor.fetchall()
        conn.close()
        for status in ticket_status:
            if status == 'collected':
                return False
            else:
                return True 
    
    except Exception as e:
        print(f"Error fetching ticket status: {e}")
        
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

def real_time_recognition(db_path, image_folder_path):
    known_face_encodings, known_face_names, known_mmu_ids = get_decode_face_data(db_path)
    
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("Error: Could not open camera.")
        return
    
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    process_this_frame = True
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        
        if process_this_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = fr.face_locations(rgb_small_frame)
            
            face_names = []
            mmu_ids = []
            
            if face_locations:
                try:
                    face_encodings = fr.face_encodings(rgb_small_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        matches = fr.compare_faces(known_face_encodings, face_encoding, tolerance=0.4)
                        name = "Unknown"
                        mmu_id = None
                        
                        if True in matches:
                            
                            check_ticket_status(db_path)
                            
                            if True:
                                first_match_index = matches.index(True)
                                mmu_id = known_mmu_ids[first_match_index]
                                name = known_face_names[first_match_index]

                                print(f"Match found: {name} (MMU ID: {mmu_id})")

                                video_capture.release()


                                cv2.destroyAllWindows()

                                cv2.waitKey(0)
                                cv2.destroyAllWindows()

                                return generate_winpass(name, mmu_id, db_path, image_folder_path)
                                                                
                        face_names.append(name)
                        mmu_ids.append(mmu_id)
                
                except Exception as e:
                    print(f"Error processing face encodings: {e}")
                    face_names = ["Error"] * len(face_locations)
                    mmu_ids = [None] * len(face_locations)
            
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
        
        process_this_frame = not process_this_frame
        
        
        cv2.imshow('Face Recognition', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


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








