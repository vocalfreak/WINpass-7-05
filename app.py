from utils.route_utils import import_csv_init, photobooth
from utils.image_utils import real_time_recognition
from utils.email_utils import send_email
from flask import Flask, render_template, redirect, url_for, request, flash 
import sqlite3
import csv
import os

app = Flask(__name__)
app.secret_key = '1q2w3xde'

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
        
@app.route('/Logout')
def logout():
    pass

@app.route('/Student-Profile')
def student_profile():
    return render_template('student_profile.html')

@app.route('/Booth-Informations')
def booth_info():
    return render_template('booth_info.html')

@app.route('/Digital-Ticket')
def digital_ticket():
    return render_template('digital_ticket.html')

@app.route('/Face-Verification')
def face_verification():
    result = real_time_recognition(db_path, image_folder_path)
    name, mmu_id, hall, career, img_path = result

    photo_filename = os.path.basename(img_path)
    photo_path     = url_for('static', filename=f"photos/{photo_filename}")

    student = {
        "student-name": name,
        "student-id": mmu_id,
        "hall": hall,       
        "career": career,
        "photo_path": photo_path,
    }
    return redirect(url_for('homepage, student=student'))

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
            cursor.execute("UPDATE user SET ticket_status='colllected' WHERE mmmu_id = ?", (mmu_id,))
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


@app.route('/Send-Email')
def email_button():
    subject    = "Win MMU is approaching!"
    body       = "We’re excited to see you at WIN 2025! Here are the details."
    image_path = r"C:\Users\chiam\Projects\WINpass-7-05\static\email.png"

    send_email(subject, body, image_path, db_path)
    flash("Invitations sent to all users!", "success")
    return redirect(url_for('admin_page'))

if __name__ == '__main__':

    #Paths 
    df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
    db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"
    image_folder_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass_training_set"

    app.run(debug=True)


