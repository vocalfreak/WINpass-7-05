# from utils.route_utils import import_csv_init
from flask import Flask, render_template, redirect, url_for, request, flash, session 
#from utils.image_utils import real_time_recognition
import sqlite3
from utils.route_utils import photobooth 

# Paths 
df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"

app = Flask(__name__)
app.secret_key = 'supersecretkey'

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

@app.route('/Booth-Information')
def booth_info():
    return render_template('booth_info.html')

@app.route('/Digital-Ticket')
def digital_ticket():
    return render_template('digital_ticket.html')

@app.route('/Face-Verification')
def face_verification():
    # real_time_recognition(db_path)
    #real_time_recognition(db_path)
    return redirect(url_for('homepage'))

@app.route('/Pre-Registration')
def pre_registration():
    pass

@app.route('/')
def admin_page():
    return render_template('admin_page.html')

@app.route('/Admin-Ui')
def admin_ui():
    return render_template('admin_ui.html')

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

@app.route('/Upload-CSV')
def upload_csv():
    import_csv_init(df_path, db_path)
    # UNCOMMENT ONCE admin_page.html IS DONE
    #return render_template('admin_page.html')
    pass

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

@app.route('/Send-Invite')
def spend_invite():
    pass

def check_credentials(ID, password):
    conn = sqlite3.connect('winpass.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE ID = ? AND password = ?", (ID, password))
    user = cursor.fetchone()
    conn.close()
    return user
    
@app.route('/')
def home():
    if 'ID' in session:
        return render_template('home.html', ID=session['ID'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ID = request.form['ID']
        password = request.form['password'] 
        
        user = check_credentials(ID, password)
        if user:
            session['ID'] = ID
            return redirect(url_for('home'))
        else:
            return "Incorrect ID or Password."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('ID', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


