import sqlite3
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrate():
    conn = sqlite3.connect('winpass.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, password FROM user")
    users = cursor.fetchall()

    for mmu_id, plaintext in users:
        if not plaintext.startswith('$2b$'):  
            hashed = hash_password(plaintext)
            cursor.execute("UPDATE user SET password = ? WHERE id = ?", (hashed, mmu_id))

    conn.commit()
    conn.close()
    print("Password migration complete.")

if __name__ == "__main__":
    migrate()