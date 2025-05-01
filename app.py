from utils.route_utils import import_csv_init, photobooth
from utils.image_utils import real_time_recognition
from utils.email_utils import send_email
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, session 
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'xp9nfcZcGQuDuoG4'

@app.route('/Landing-Page')
def homepage():
    return render_template("landing_page.html")

@app.route('/Login-Users', methods=['GET', 'POST'])
def login_users():
    if request.method == 'POST':
        mmu_id = request.form.get('mmu_id')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, email, career, faculty, hall FROM user WHERE mmu_id = ? AND password = ?", (mmu_id, password))
        user = cursor.fetchone() 

        if user:
            session['mmu_id'] = mmu_id
            session['name'] = user[1]
            session['email'] = user[2] 
            session['career'] = user[3] 
            session['faculty'] = user[4] 
            session['hall'] = user[5]
            cursor.execute("UPDATE user SET ticket_status='colllected' WHERE mmu_id = ?", (mmu_id,))
            conn.commit()
            conn.close()
            
            return redirect(url_for('homepage'))
    
    
    return render_template('login_users.html')

@app.route('/Login-Admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        mmu_id = request.form.get('mmu_id')
        password = request.form.get('password')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM admin WHERE mmu_id = ? AND password = ?", (mmu_id, password))
        admin = cursor.fetchone() 

        if admin:
            conn.close()
            
            # CHANGE TO admin_page.html LATER 
            return redirect(url_for('homepage'))
        
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

@app.route('/')
def admin_landing():
    return render_template('admin_landing.html')

@app.route('/Admin-Page')
def admin_page():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT mmu_id, name, career, faculty, campus, email, goodies_status, badge_status, ticket_status FROM user")
    students = cursor.fetchall()
    conn.close()
    return render_template('admin_page.html', students=students)

@app.route('/Admin-Home')
def home():
    return render_template('admin_landing.html')

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
app.config['UPLOAD_FOLDER'] = 'face'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/Pre_Registration_page', methods=['POST', 'GET'])
def pre_registration_page():
    if request.method == 'POST':
        full_name = request.form['student-name']
        student_id = request.form['ID']
        email_address = request.form['email-address']
        phone_num = request.form['phone-number']
        face_pic = request.files['filename']

        if face_pic and allowed_file(face_pic.filename):
            filename = secure_filename(face_pic.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            face_pic.save(filepath)
        else:
            filepath = None  

        print(f"Full Name: {full_name}")
        print(f"Student ID: {student_id}")
        print(f"Email: {email_address}")
        print(f"Phone: {phone_num}")
        print(f"File path: {filepath}") 

        return "Form submitted successfully!"

    return render_template('pre_registration_page.html')



@app.route('/Email')
def email():
    return render_template("email.html")

if __name__ == '__main__':

    #Paths 
    df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
    db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"
    image_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass_training_set"

    app.run(debug=True)




