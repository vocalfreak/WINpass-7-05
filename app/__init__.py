import sqlite3
import os 

db_path = os.path.join(os.path.dirname(__file__), 'winpass.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mmu_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    hall TEXT,
    career TEXT,
    faculty TEXT,
    campus TEXT,
    face_data BLOB,
    qr_code TEXT,
    ticket_path TEXT,

    goodies_checkin TEXT DEFAULT 'Pending',
    badge_checkin TEXT DEFAULT 'Pending',
    ticket_checkin TEXT DEFAULT 'Pending'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mmu_id TEXT NOT NULL,
    email TEXT
)
''')

conn.commit()
conn.close()