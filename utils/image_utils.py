import os
from PIL import Image, ImageOps
import face_recognition as fr
import sqlite3
import numpy as np
import cv2 

def resize_image(img_path, size=(250, 250), fill_color=(0, 0, 0)):

    img = Image.open(img_path)
    img.thumbnail(size, Image.LANCZOS)
    delta_w = size[0] - img.size[0]
    delta_h = size[1] - img.size[1]
    padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)
    return ImageOps.expand(img, padding, fill=fill_color)

def get_face_encodings_folders(image_folder_path, db_path):

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

def get_decode_face_data(db_path):
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, face_data FROM user WHERE face_data IS NOT NULL")
    users = cursor.fetchall()
    conn.close()

    known_face_encodings = []
    known_face_names = []
    known_face_ids = []

    for user_id,name, face_data_blob in users:
        if face_data_blob:
            encodings_array = np.frombuffer(face_data_blob, dtype=np.float64)
            stored_encodings = encodings_array.reshape(-1, 128)

            for encoding in stored_encodings:
                known_face_encodings.append(encoding)
                known_face_names.append(name)
                known_face_ids.append(user_id)

    print(f"Loaded {len(known_face_encodings)} face encodings from {len(users)} users")
    return known_face_encodings, known_face_names, known_face_ids

def real_time_recognition(db_path):
    known_face_encodings, known_face_names, known_face_ids = get_decode_face_data(db_path)
    
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("Error: Could not open camera.")
        return
    
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    processed_users = set()
    
    process_this_frame = True
    
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        if process_this_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = fr.face_locations(rgb_small_frame)
            
            face_names = []
            face_user_ids = []
            
            if face_locations:
                try:
                    face_encodings = fr.face_encodings(rgb_small_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        matches = fr.compare_faces(known_face_encodings, face_encoding, tolerance=0.4)
                        name = "Unknown"
                        user_id = None
                        
                        if True in matches:
                            first_match_index = matches.index(True)
                            name = known_face_names[first_match_index]
                            user_id = known_face_ids[first_match_index]
                            
                            if user_id and user_id not in processed_users:
                                processed_users.add(user_id)
                                print(f"New user detected: {name} (ID: {user_id})")
                        
                        face_names.append(name)
                        face_user_ids.append(user_id)
                
                except Exception as e:
                    print(f"Error processing face encodings: {e}")
                    face_names = ["Error"] * len(face_locations)
                    face_user_ids = [None] * len(face_locations)
            
            # CONNECT TO DATABASE LATER
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


def photobooth():
    
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
            img_name = "opencv_frame_{}.png".format(img_counter)
            cv2.imwrite(img_name,frame)
            print("Photo taken")
            img_counter+=1

    cam.release()
    cv2.destroyAllWindows()





