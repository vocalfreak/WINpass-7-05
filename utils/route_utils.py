import os
from PIL import Image, ImageOps
import sqlite3
import numpy as np
import cv2 
import csv
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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
                hash_password(row['password']),
                row['career'],
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

def get_timeslot(db_path):

    slot_1 = 0
    slot_2 = 0
    slot_3 = 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timeslot FROM user")
    results = cursor.fetchall()

    for row in results:
        timeslot_value = row[0]  
            
        if timeslot_value == 'slot_1' or timeslot_value == 1:
            slot_1 += 1
        elif timeslot_value == 'slot_2' or timeslot_value == 2:
            slot_2 += 1
        elif timeslot_value == 'slot_3' or timeslot_value == 3:
            slot_3 += 1

    conn.close()
    time_slots = [slot_1, slot_2, slot_3]
    return slot_1, slot_2, slot_3, time_slots

def get_timeslot_status(timeslots):
    timeslots_status = []
    for count in timeslots:
        if count < 2:
            timeslots_status.append("green")
        elif count < 5:
            timeslots_status.append("yellow")
        else:
            timeslots_status.append("red")
    return timeslots_status

def get_queue_time(db_path):      

    hall_occupancy = 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_status FROM user")
    results = cursor.fetchall()

    for status in results:
        if status[0] == "collected":
            hall_occupancy += 1
        else:
            continue 
    
    queue_time = hall_occupancy * 2 

    conn.close()

    return queue_time, hall_occupancy
            

                
