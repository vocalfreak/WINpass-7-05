import sqlite3
import csv

HALLS = ["Samudera", "Inderasakti", "Kasturi", "Laksamana", "Mahamiru", "Rajawali"]

#chat suggest to create a table eventho its already created
def init_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    #sql command
    cursor.execute('''
    CREATE TABLE IF NOT EXIST user (
        name TEXT,
        mmu_id TEXT PRIMARY KEY,
        email TEXT,
        password TEXT,
        hall TEXT,
        career TEXT,
        faculty TEXT,
        campus TEXT,
    )
    ''')

    conn.commit()
    #save all the changes I made to the database
    conn.close()
    #close the connection to the database file

#PRIMARY KEY : helps the database identify each student

def import_users_with_halls(csv_path, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor
    
    try: #attempt to run the code safely
        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for index, row in enumerate(reader): #index: row no, row: actual student data (as a dictionary)
                hall = HALLS[index % len(HALLS)]  # assign hall in order (looping)

                cursor.execute('''
                    INSERT OR REPLACE INTO user (name, mmu_id, email, career, faculty, campus, hall)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['name'],
                    row['mmu_id'],
                    row['email'],
                    row['password'],
                    row['hall'],
                    row['career'],
                    row['faculty'],
                    row['campus'],
                    hall
                ))
        
        conn.commit()
        print("Import complete.")

    except Exception as e:
        print(" Error:", e)
    
    finally:
        conn.close()

def view_all_users(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user")  #sends a command to the database 
                                          #SELECT * means: grab all columns (name, mmu_id, email, etc.)
                                          #FROM user means: look at the user table I created earlier

    users = cursor.fetchall()   #a list of student records (user)
    
    for user in users:
        print(user) #output
    
    conn.close()
   
if __name__ == '__main__':
    db_file = 'winpass.db'         #sqlite db file
    csv_file = 'students.csv'       #csv file with student data

    init_database(db_file)      # creates the database file #creates a table named user inside it
    import_users_with_halls(csv_file, db_file)      #automatically assigns each student a hall
    view_all_users(db_file)     #pulls out and displays all students from the database
    