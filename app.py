from utils.route_utils import import_csv_init, photobooth, get_timeslot, get_timeslot_status, get_queue_time 
from utils.image_utils import real_time_recognition, get_winpass_info, badge_qr, get_face_encodings_folders, goodies_qr, image_to_base64
from utils.email_utils import send_email, send_email_ticket
from datetime import datetime
from utils.instagram_utils import get_weekend_filter, get_tmr_filter
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, session 
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from datetime import timedelta
from utils.route_utils import hash_password, check_password, bcrypt
from html2image import Html2Image

app = Flask(__name__)

app.secret_key = 'xp9nfcZcGQuDuoG4'
app.permanent_session_lifetime = timedelta(minutes=20) 

@app.route('/')
def homepage():
    slot_1, slot_2, slot_3, time_slots = get_timeslot(db_path)

    timeslot_status = get_timeslot_status(time_slots)

    queue_time, hall_occupancy = get_queue_time(db_path)

    timeslots=[
        {'status': timeslot_status[0], 'count': slot_1, 'time': '10:00 AM - 12:00 PM'},
        {'status': timeslot_status[1], 'count': slot_2, 'time': '12:00 PM - 2:00 PM'},
        {'status': timeslot_status[2], 'count': slot_3, 'time': '2:00 PM - 4:00 PM'}
    ]

    queue= {
        'occupancy': hall_occupancy, 
        'queue_time': queue_time
    }
    return render_template("landing_page.html", timeslots=timeslots, queue=queue)

@app.route('/admin_landing')
def admin_landing():
    slot_1, slot_2, slot_3, time_slots = get_timeslot(db_path)

    timeslot_status = get_timeslot_status(time_slots)

    queue_time, hall_occupancy = get_queue_time(db_path)

    timeslots=[
        {'status': timeslot_status[0], 'count': slot_1, 'time': '10:00 AM - 12:00 PM'},
        {'status': timeslot_status[1], 'count': slot_2, 'time': '12:00 PM - 2:00 PM'},
        {'status': timeslot_status[2], 'count': slot_3, 'time': '2:00 PM - 4:00 PM'}
    ]

    queue= {
        'occupancy': hall_occupancy, 
        'queue_time': queue_time
    }
    return render_template("admin_landing.html", timeslots=timeslots, queue=queue)


@app.route('/Login-Users', methods=['GET', 'POST'])
def login_users():
    if request.method == 'POST':
        mmu_id = request.form.get('mmu_id').strip()
        password = request.form.get('password').strip()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name, email, password FROM admin WHERE mmu_id = ?", (mmu_id,))
        admin = cursor.fetchone()

        if admin and check_password(password, admin[2]):
           session.permanent = True
           session['mmu_id'] = mmu_id
           session['name'] = admin[0]
           session['email'] = admin[1]
           conn.close()
           return redirect(url_for('admin_landing')) 

        cursor.execute("SELECT id, name, email, career, faculty, hall, password FROM user WHERE mmu_id = ?", (mmu_id,))
        user = cursor.fetchone()

        if user and check_password(password, user[6]):
           session.permanent = True
           session['mmu_id'] = mmu_id
           session['name'] = user[1]
           session['email'] = user[2]
           session['career'] = user[3]
           session['faculty'] = user[4]
           session['hall'] = user[5]
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
            'hall': user[5],
        }

        avatar_rel_path = get_student_avatar(user_data['name'], user_data['mmu_id'], image_folder_path)
        if avatar_rel_path:
            session['avatar'] = avatar_rel_path
        else:
            session.pop('avatar', None)

    else:
        user_data = None
        session.pop('avatar', None)

    return render_template('student_profile.html', user=user_data)

@app.route('/Booth-Informations')
def booth_info():
    return render_template('booth_info.html')

@app.route('/Digital-Ticket')
def digital_ticket():
    if 'mmu_id' not in session:
        return redirect(url_for('login_users')) 
    
    mmu_id = (session['mmu_id'])

    result = get_winpass_info(mmu_id, db_path, image_folder_path)
    name, mmu_id, hall, career, img_path = result

    rel_path = os.path.relpath(img_path, start=image_folder_path).replace('\\','/')
    photo_url = url_for('photos', filename=rel_path)

    qr_path = f"qr_codes/{mmu_id}.png"

    student = {
        "name": name,
        "mmu_id": mmu_id,
        "hall": hall,       
        "career": career,
        "photo_path": photo_url,
        "qr_path": qr_path
    }

    return render_template("digital_ticket.html", student=student)


@app.route('/photos/<path:filename>')
def photos(filename):
    return send_from_directory(image_folder_path, filename)

@app.route('/Face-Verification')
def face_verification():
    result = real_time_recognition(db_path, image_folder_path)
    session['result'] = result
    name, mmu_id, hall, career, img_path, qr_path = result

    session['mmu_id'] = mmu_id

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

    session['qr_path'] = qr_path

    return render_template("digital_ticket_generation.html", student=student)

@app.route('/Comfirm')
def comfirm_button():
    result = (session['result'])

    if result:
        name, mmu_id, hall, career, img_path, qr_path = result 

        photo = image_to_base64(img_path)
        qr = image_to_base64(os.path.join(f"static/qr_codes/{mmu_id}.png"))

        app_dir = os.path.dirname(os.path.abspath(__file__))

        batik_path = os.path.join(app_dir, "static", "images", f"{hall}_batik.png")
        mmu_logo_path = f"static/img_mmu.png" 
        hall_logo_path = os.path.join(app_dir, "static", "images", f"{hall}_logo.png")

        batik = image_to_base64(batik_path)
        mmu_logo = image_to_base64(mmu_logo_path)
        hall_logo = image_to_base64(hall_logo_path)

        student = {
            "name": name,
            "mmu_id": mmu_id,
            "hall": hall,       
            "career": career,
            "photo_path": photo,
            "qr_path": qr,
            "batik_path": batik,
            "mmu_logo_path": mmu_logo,
            "hall_logo_path": hall_logo
            }
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE user SET ticket_status='collected' WHERE mmu_id = ?", (mmu_id,))
        conn.commit()

        html_digital_ticket = render_template("digital_ticket_screenshot.html", student=student)

        output_dir = "static/digital_tickets"
        os.makedirs(output_dir, exist_ok=True)
        image_filename = f"{mmu_id}_winpass.png"
        image_path = os.path.join(output_dir, image_filename)

        hti = Html2Image(output_path=output_dir)
        hti.screenshot(html_str=html_digital_ticket, save_as=image_filename, size=(550, 600))

        send_email_ticket(image_path, db_path, mmu_id, name)

        conn.close()

        session.pop('mmu_id', None)
        session.pop('qr_path', None)
        session.pop('result', None)

        return redirect(url_for('admin_landing'))

    session.pop( 'mmu_id', None)
    session.pop('qr_path', None)
    session.pop('result', None)

    return redirect(url_for('admin_landing')) 

@app.route('/Reject')
def reject_button():
    qr_path = session['qr_path']
    
    qr_path = os.path.join(qr_folder_path, qr_path)
    os.remove(qr_path)
    
    session.pop( 'mmu_id', None)
    session.pop('qr_path', None)
    session.pop('result', None)

    return face_verification()

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
        action = request.form.get('action')
        mmu_id = request.form['mmu_id'] 

        if action == 'update':
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

            flash("Student information updated successfully.", "success")
            return redirect(url_for('admin_page'))

        elif action == 'delete':
            cursor.execute("DELETE FROM user WHERE mmu_id = ?", (mmu_id,))
            conn.commit()
            conn.close()

            flash("Student deleted successfully.", "success")
            return redirect(url_for('admin_page'))

    cursor.execute("SELECT mmu_id, name, career, faculty, campus, email FROM user WHERE mmu_id=?", (mmu_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return "Student not found", 404

    return render_template('edit_student.html', student=student)

@app.route('/Self-Service', methods=['GET', 'POST'])
def self_service():
    if request.method == 'POST':
        mmu_id = request.form.get('mmu_id')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, password FROM user WHERE mmu_id = ?", (mmu_id,))
        user = cursor.fetchone()

        if user and check_password(password, user[1]):
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

    send_email(subject, body, image_path, db_path, html_template_path)
    flash("Invitations sent to all users!", "success")
    return redirect(url_for('admin_page'))

Picture_folder = 'winpass_training_set'
app.config['UPLOAD_FOLDER'] = Picture_folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_user(nonce, face_data, size=None, timeslot=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE user set face_data = ?, size = ?, timeslot = ? WHERE nonce = ?", (face_data, size, timeslot, nonce))
    conn.commit()
    conn.close()

@app.route('/Pre_Registration_page', methods=['POST', 'GET'])
def pre_registration_page():
    token = request.args.get('token') or request.form.get('token')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT mmu_id, name FROM user WHERE nonce = ?", (token,))
    user = cursor.fetchone()
    print(f"User full name: {user}")
    conn.close()

    if user is None:
        return "Invalid token or user not found", 404
    
    mmu_id, name = user


    if request.method == 'POST':
        name = name.strip().replace(" ", "_")
        size = request.form.get('size')
        timeslot = request.form.get('timeslot')
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

        update_user(token, face_data, size, timeslot)

        return "Form submitted successfully!"

    return render_template('pre_registration_page.html', token=token, name=name)

@app.route('/Announcement_student')
def announcement_student():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM announcements ORDER BY time DESC")
    announcements = cursor.fetchall()
    conn.close()
    return render_template('announcement_student.html', announcements=announcements)

@app.route('/Announcement_admin')
def announcement_admin():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, message FROM announcements ORDER BY time DESC")
    announcements = cursor.fetchall()
    conn.close()
    return render_template('announcement_admin.html', announcements=announcements)

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM announcements WHERE id = ?", (id,))
        conn.commit()
    except Exception as e:
        conn.close()
        return f"Deletion failed: {e}"
    conn.close()
    return redirect(url_for('announcement_admin'))

@app.route('/update/<int:id>', methods=['GET','POST'])
def update(id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if request.method == 'POST':
        message = request.form['message']
        try:
            cursor.execute("UPDATE announcements SET message = ? WHERE id = ?", (message, id))
            conn.commit()
            flash("Updated successfully")
        except Exception as e:
            conn.close()
            return f"Update failed: {e}"
        conn.close()
        return redirect(url_for('announcement_admin'))

    else:
        cursor.execute("SELECT * FROM announcements WHERE id = ?", (id,))
        announcement = cursor.fetchone()
        conn.close()
        if announcement:
            return render_template('update_announcement.html', announcement=announcement)
        else:
            return "Announcement not found", 404


@app.route('/post_announcement', methods=['GET', 'POST'])
def post_announcement():
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO announcements (message) VALUES (?)", (message,))
            conn.commit()
            conn.close()
            return redirect(url_for('announcement_admin'))
    return render_template('post_announcement.html')


@app.route('/Checklist_page', methods=['POST', 'GET'])
def register_checklist():
    if request.method == 'POST':
        mmu_id = request.form.get('ID')
        goodies_status = request.form.get('goodies_status')
        badge_status = request.form.get('badge_status')
        ticket_status = request.form.get('ticket_status')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if goodies_status is not None:
            cursor.execute("UPDATE user set goodies_status = ? WHERE mmu_id = ?", (goodies_status, mmu_id))
        if badge_status is not None:
            cursor.execute("UPDATE user set badge_status = ? WHERE mmu_id = ?", (badge_status, mmu_id))
        if ticket_status is not None:
            cursor.execute("UPDATE user set ticket_status = ? WHERE mmu_id = ?", (ticket_status, mmu_id))
        conn.commit()
        conn.close()

        return "Checklist updated successfully!"
    return render_template('qr.html')


@app.route('/Scan_goodies')
def scan_goodies():
    mmu_id = goodies_qr(db_path)

    if not mmu_id:
        return "No QR code detected or failed to update database."

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT size FROM user WHERE mmu_id = ?", (mmu_id,))
        result = cursor.fetchone()
        conn.close()

        size = result[0] if result else "Not Found"
        return f"T-shirt size for {mmu_id}: {size}"

    except Exception as e:
        print("Database error:", e)
        return "Failed to fetch T-shirt size."


@app.route('/Scan_badge')
def scan_badge():
    badge_qr(db_path)
    return render_template('qr.html')


@app.route('/Email')
def email():
    return render_template("email.html")

def get_student_avatar(name, mmu_id, image_folder_path):
    person_folder_path = os.path.join(image_folder_path, name.replace(' ', '_'))
    if os.path.exists(person_folder_path):
        image_files = [f for f in os.listdir(person_folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if image_files:
            first_img = image_files[0]
            img_path = os.path.join(person_folder_path, first_img)
            rel_path = os.path.relpath(img_path, start=image_folder_path).replace("\\", "/")
            return rel_path
    return None

@app.route('/events')
def events_page():
    filter_type = request.args.get("filter")
    today = datetime.today().date()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT caption, shortCode, details, title, date, time, location, ownerFullName FROM instagram")
    rows = cursor.fetchall()
    conn.close()

    if filter_type == "tomorrow":   
        daterange = [get_tmr_filter(today)]
    elif filter_type == "weekend":
        daterange = get_weekend_filter(today)
    else:
        daterange = None

    events = []
    for row in rows:
        date = row[4]

        if not date:
            continue 
        
        eventdate = datetime.strptime(row[4], "%Y%m%d").date()  
        
        if filter_type == "past":
            if eventdate >= today:
                continue
        
        elif filter_type == "all":
            if eventdate <= today:
                continue 

        else: 
            if daterange and eventdate not in daterange:
                continue

        days_ago = (today - eventdate).days

        events.append({
            "caption": row[0],
            "shortCode": row[1],
            "details": row[2],
            "title": row[3],
            "date": row[4],
            "time": row[5],
            "location": row[6],
            "days_ago": days_ago,
            "host" : row[7]
        })

    return render_template("event_page.html", events=events, past_view=(filter_type == "past"))

@app.route('/event/<shortCode>')
def event_detail(shortCode):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT caption, shortCode, details, title, date, time, location, ownerFullName FROM instagram WHERE shortCode = ?", (shortCode,))
    rows = cursor.fetchall()
    conn.close()

    details = []
    for row in rows:
        details.append({
            "caption": row[0],
            "shortCode": row[1],
            "details": row[2],
            "title": row[3],
            "date": row[4],
            "time": row[5],
            "location": row[6],
            "host" : row[7]
        })

    return render_template("event_details.html", details=details)


def get_leaderboard():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, points FROM halls ORDER BY points DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route('/leaderboard')
def leaderboard():
    halls = get_leaderboard()
    return render_template('leaderboard.html', halls=halls)

@app.route('/update', methods=['POST'])
def update_points():
    hall_name = request.form['hall']
    points = int(request.form['points'])

    with sqlite3.connect('leaderboard.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE halls SET points = points + ? WHERE name = ?", (points, hall_name))
        conn.commit()

    return redirect('/leaderboard')

if __name__ == '__main__':

    #Paths 
    # df_path = r"C:\Users\adria\Projects\WINpass-7-05\Test_George.csv"
    # db_path = r"C:\Users\adria\Projects\WINpass-7-05\winpass.db"
    # image_folder_path = r"C:\Users\adria\Projects\WINpass-7-05\winpass_training_set"
    # qr_folder_path = r"C:\Users\adria\Projects\WINpass-7-05\static\qr_codes"
    # html_template_path = r'C:\Users\adria\Projects\WINpass-7-05\templates\email.html'

    # db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"
    # image_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass_training_set"
    # df_path = r"C:\Users\chiam\Projects\WINpass-7-05\Test_George.csv"
    # qr_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\static\qr_codes"
    # html_template_path = r'C:\Users\chiam\Projects\WINpass-7-05\templates\email.html'


    db_path = "winpass.db"
    image_folder_path = "winpass_training_set"
    html_template_path = "templates/email.html"
    qr_folder_path = "static/qr_codes"
    df_path = "Test_George.csv"



    # db_path = r"C:\Users\user\projects\WINpass-7-05\winpass.db"
    # db_path = r"C:\Users\user\Desktop\mini\WINpass-7-05\leaderboard.db"


    
    DB_FILE = 'leaderboard.db'

    app.run(debug=True)


