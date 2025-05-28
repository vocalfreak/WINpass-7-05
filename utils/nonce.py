import sqlite3
import secrets

db_path = r"C:\Mini IT\WINpass-7-05\winpass.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT mmu_id FROM user")
users = cursor.fetchall()

for (mmu_id,) in users:
    nonce = secrets.token_urlsafe(16)
    cursor.execute("UPDATE user SET nonce = ? WHERE mmu_id = ?", (nonce, mmu_id))

conn.commit()
conn.close()
print("done")
