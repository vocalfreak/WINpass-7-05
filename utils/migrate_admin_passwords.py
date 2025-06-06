import sqlite3
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrate():
    conn = sqlite3.connect('winpass.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, password FROM admin")
    admins = cursor.fetchall()

    for mmu_id, plaintext in admins:
        if not plaintext.startswith('$2b$'):  
            hashed = hash_password(plaintext)
            cursor.execute("UPDATE admin SET password = ? WHERE id = ?", (hashed, mmu_id))

    conn.commit()
    conn.close()
    print("Password migration for admins complete.")

if __name__ == "__main__":
    migrate()
