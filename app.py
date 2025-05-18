from utils.route_utils import import_csv_init, photobooth
from utils.image_utils import real_time_recognition
from utils.image_utils import get_face_encodings_folders
from utils.image_utils import ticket_qr, badge_qr, goodies_qr
#from utils.email_utils import send_email
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, session 
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'xp9nfcZcGQuDuoG4'
db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"

@app.route('/Landing-Page')
def homepage():
    return render_template("landing_page.html")

@app.route('/Login-Users', methods=['GET', 'POST'])
def login_users():
    if request.method == 'POST':
        mmu_id = request.form.get('mmu_id').strip()
        password = request.form.get('password').strip()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name, email FROM admin WHERE mmu_id = ? AND password = ?", (mmu_id, password))
        admin = cursor.fetchone()

        if admin:
            session['mmu_id'] = mmu_id
            session['name'] = admin[0]
            session['email'] = admin[1]
            conn.close()
            return redirect(url_for('admin_landing')) 

       
        cursor.execute("SELECT id, name, email, career, faculty, hall FROM user WHERE mmu_id = ? AND password = ?", (mmu_id, password))
        user = cursor.fetchone()

        if user:
            session['mmu_id'] = mmu_id
            session['name'] = user[1]
            session['email'] = user[2]
            session['career'] = user[3]
            session['faculty'] = user[4]
            session['hall'] = user[5]

            cursor.execute("UPDATE user SET ticket_status='collected' WHERE mmu_id = ?", (mmu_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('homepage'))

        else:
            conn.close()
            flash('Invalid MMU ID or password. Please try again.', 'error')
            return redirect(url_for('login_users'))

    return render_template('login_users.html')

        
@app.route('/Logout', methods=['POST'])
def logout():
    session.clear()  
    
    flash("You have been logged out.", "success")
    
    return redirect(url_for('homepage'))

@app.route('/Student-Profile')
def student_profile():
    if 'mmu_id' not in session:
        return redirect(url_for('login_users')) 
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, mmu_id, email, career, faculty, hall FROM user WHERE mmu_id = ?",
        (session['mmu_id'],)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        user_data = {
            'name': user[0],
            'mmu_id': user[1],
            'email': user[2],
            'career': user[3],
            'faculty': user[4],
            'hall': user[5]
        }
    else:
        user_data = None

    return render_template('student_profile.html', user=user_data)

@app.route('/Booth-Informations')
def booth_info():
    return render_template('booth_info.html')

@app.route('/Digital-Ticket')
def digital_ticket():
    return render_template('digital_ticket.html')

@app.route('/photos/<path:filename>')
def photos(filename):
    return send_from_directory(image_folder_path, filename)

@app.route('/')
def temporary():
    return render_template('landing_page.html')

@app.route('/Face-Verification')
def face_verification():
    result = real_time_recognition(db_path, image_folder_path)
    name, mmu_id, hall, career, img_path, qr_path = result

    rel_path = os.path.relpath(img_path, start=image_folder_path).replace('\\','/')
    photo_url = url_for('photos', filename=rel_path)

    student = {
        "name": name,
        "mmu_id": mmu_id,
        "hall": hall,       
        "career": career,
        "photo_path": photo_url,
        "qr_path": qr_path
    }
    return render_template("digital_ticket.html", student=student)

@app.route('/Pre-Registration')
def pre_registration():
    pass

@app.route('/admin_landing')
def admin_landing():
    return render_template('admin_landing.html') 


@app.route('/Admin-Page')
def admin_page():
    search_query = request.args.get('search' , '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if search_query:
        cursor.execute("SELECT mmu_id, name, career, faculty, campus, email, goodies_status, badge_status, ticket_status FROM user WHERE name LIKE ? OR mmu_id LIKE ?", ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        cursor.execute("SELECT mmu_id, name, career, faculty, campus, email, goodies_status, badge_status, ticket_status FROM user")

    students = cursor.fetchall()
    updated_students = []

    for student in students:
        mmu_id, name, career, faculty, campus, email, goodies_status, badge_status, ticket_status = student
        statuses = [goodies_status, badge_status, ticket_status]
        booth_status = f"{statuses.count('collected')}/3"
        updated_students.append((mmu_id, name, career, faculty, campus, email, booth_status))


    conn.close()
    return render_template('admin_page.html', students=updated_students)

@app.route('/edit-student', methods=['GET', 'POST'])
def edit_student():
    mmu_id = request.args.get('mmu_id')
    if not mmu_id:
        return redirect(url_for('admin_page'))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        career = request.form['career']
        faculty = request.form['faculty']
        campus = request.form['campus']
        email = request.form['email']

        cursor.execute("""
            UPDATE user 
            SET name=?, career=?, faculty=?, campus=?, email=?
            WHERE mmu_id=?
        """, (name, career, faculty, campus, email, mmu_id))

        conn.commit()
        conn.close()
        return redirect(url_for('admin_page'))

    cursor.execute("SELECT mmu_id, name, career, faculty, campus, email FROM user WHERE mmu_id=?", (mmu_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return "Student not found", 404

    return render_template('edit_student.html', student=student)

@app.route('/Admin-Home')
def home():
    return render_template('landing_page.html')

@app.route('/Self-Service', methods=['GET', 'POST'])
def self_service():
    if request.method == 'POST':
        mmu_id = request.form.get('mmu_id')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM user WHERE mmu_id = ? AND password = ?", (mmu_id, password))
        user = cursor.fetchone() 

        if user:
            cursor.execute("UPDATE user SET ticket_status='colllected' WHERE mmu_id = ?", (mmu_id,))
            conn.commit()
            conn.close()
            
            # CHANGE TO TICKET PAGE LATER
            return redirect(url_for('homepage'))
    
    # UNCOMMENT ONCE self_service.html IS DONE
    #return render_template('self_service.html')

@app.route('/Import-CSV', methods=['POST'])
def import_csv():
    if request.method == 'POST':
        import_csv_init(df_path, db_path)
        flash('CSV imported successfully!', 'success')
    return admin_page()

@app.route('/Photobooth_Page')
def photobooth_page():
    return render_template('photobooth_page.html')

@app.route('/Photobooth_Camera')
def photobooth_camera():
    photobooth()
    return render_template('photobooth_page.html')

@app.route('/Editing_Page')
def editing_page():
    return render_template('editing_page.html')

@app.route('/Send-Email')
def email_button():
    subject    = "Win MMU is approaching!"
    body       = "We’re excited to see you at WIN 2025! Here are the details."
    image_path = r"C:\Users\chiam\Projects\WINpass-7-05\static\email.png"

    send_email(subject, body, image_path, db_path)
    flash("Invitations sent to all users!", "success")
    return redirect(url_for('admin_page'))

@app.route('/Checklist_page', methods=['POST', 'GET'])
def register_checklist():
    if request.method == 'POST':
        mmu_id = request.form.get('ID')
        goodies_status = request.form.get('goodies_status', 'Pending')
        badge_status = request.form.get('badge_status', 'Pending')
        ticket_status = request.form.get('ticket_status', 'Pending')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE user set goodies_status = ?, badge_status = ?, ticket_status = ? WHERE mmu_id = ?", (goodies_status, badge_status, ticket_status, mmu_id))
        conn.commit()
        conn.close()

        return "Checklist updated successfully!"
    return render_template('qr.html')

@app.route('/Scan_tickets')
def scan_tickets():
    ticket_qr()
    ticket_status = request.form.get('ticket_status', 'Pending')

    ticket = request.args.get('ticket')
    if not ticket:
        return "No ticket detected. Please retry or meet the admin to verify", 400
    mmu_id = ticket
    global db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE user set ticket_status = ? WHERE mmu_id = ?", (ticket_status, mmu_id))
    conn.commit()
    conn.close()

    return render_template('qr.html')

@app.route('/Scan_goodies')
def scan_goodies():
    goodies_qr()
    goodies_status = request.form.get('ticket_status', 'Pending')

    ticket = request.args.get('ticket')
    if not ticket:
        return "No ticket detected. Please retry or meet the admin to verify", 400
    mmu_id = ticket
    global db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE user set goodies_status = ? WHERE mmu_id = ?", (goodies_status, mmu_id))
    conn.commit()
    conn.close()

    return render_template('qr.html')

@app.route('/Scan_badge')
def scan_badge():
    badge_qr()
    badge_status = request.form.get('ticket_status', 'Pending')

    ticket = request.args.get('ticket')
    if not ticket:
        return "No ticket detected. Please retry or meet the admin to verify", 400
    mmu_id = ticket
    global db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE user set badge_status = ? WHERE mmu_id = ?", (badge_status, mmu_id))
    conn.commit()
    conn.close()

    return render_template('qr.html')


Picture_folder = 'winpass_training_set'
app.config['UPLOAD_FOLDER'] = Picture_folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_user(mmu_id, face_data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET face_data = ? WHERE mmu_id = ?", (face_data, mmu_id))
    conn.commit()
    conn.close()

@app.route('/Pre_Registration_page', methods=['POST', 'GET'])
def pre_registration_page():
    if request.method == 'POST':
        mmu_id = request.form['ID']
        name = request.form['name'].strip().replace(" ", "_")
        image_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], name)
        os.makedirs(image_folder_path, exist_ok=True)
        face_1 = request.files['filename1']
        face_2 = request.files['filename2']

        filepath_1 = filepath_2 = None


        if face_1 and allowed_file(face_1.filename):
            filename1 = f"{name}_0001.jpg"
            filepath_1 = os.path.join(image_folder_path, filename1)
            face_1.save(filepath_1)
        else:
            print("Unable to save the first picture")
 
        if face_2 and allowed_file(face_2.filename):
            filename2 = f"{name}_0002.jpg"
            filepath_2 = os.path.join(image_folder_path, filename2)
            face_2.save(filepath_2)
        else:
            print("Unable to save the second picture")


        print(f"Student ID: {mmu_id}")
        face_code = get_face_encodings_folders(image_folder_path)

        if face_code is None:
            print("No valid face encodings found.")
            return "Error: Face not detected in one or both images.", 400

        print(f"Combined face encoding: {face_code}")

        face_data = face_code.tobytes()

        update_user(mmu_id, face_data)

        return "Form submitted successfully!"

    return render_template('pre_registration_page.html')


@app.route('/Email')
def email():
    return render_template("email.html")


def get_leaderboard():
    conn = sqlite3.connect('winpass.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, gold, silver, bronze, points FROM hall ORDER BY points DESC")
    halls = cursor.fetchall()
    conn.close()
    return halls

def update_points(hall_id, medal):
    points_map = {'gold': 5, 'silver': 3, 'bronze': 1}
    if medal not in points_map:
        return

    conn = sqlite3.connect('winpass.db')
    cursor = conn.cursor()
    cursor.execute(f"""
        UPDATE hall
        SET {medal} = {medal} + 1,
            points = points + ?
        WHERE id = ?
    """, (points_map[medal], hall_id))
    conn.commit()
    conn.close()

@app.route('/leaderboard')
def leaderboard():
    halls = get_leaderboard()
    return render_template('leaderboards.html', halls=halls)

@app.route('/add/<int:hall_id>/<medal>', methods=['POST'])
def add_medal(hall_id, medal):
    update_points(hall_id, medal)
    return redirect(url_for('leaderboard'))

@app.route('/update', methods=['POST'])
def update():
    hall_id = request.form['hall']
    medal = request.form['medal']
    update_points(hall_id, medal)
    return redirect(url_for('leaderboard'))

if __name__ == '__main__':

    #Paths 
    df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
    #db_path = r"C:\Users\adria\Projects\WINpass-7-05\winpass.db"
    #image_folder_path = r"C:\Users\adria\Downloads\winpass_training_set"
    # db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"
    db_path = r"C:\Users\user\projects\WINpass-7-05\winpass.db"
    image_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass_training_set"
    #db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"
    #db_path = r"C:\Users\adria\Projects\WINpass-7-05\winpass.db"
    #image_folder_path = r"C:\Users\adria\Downloads\winpass_training_set"
    #db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"
    db_path = r"C:\Foundation\WINpass\WINpass-7-05\winpass.db"
    image_folder_path = r"C:\Foundation\WINpass\WINpass-7-05\winpass_training_set"
    #image_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass_training_set"

    app.run(debug=True)




