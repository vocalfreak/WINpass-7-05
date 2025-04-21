from utils.route_utils import import_csv_init
from flask import Flask, render_template, redirect, url_for
from utils.image_utils import real_time_recognition 

# Paths 
df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
db_path = r"C:\Users\chiam\Projects\WINpass-7-05\winpass.db"

#import_csv_init(df_path, db_path)

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("landing_page.html")

@app.route('/Student-Profile')
def student_profile():
    real_time_recognition(db_path)
    return redirect(url_for('homepage'))

@app.route('/Booth-Information')
def booth_info():
    return render_template('booth_info.html')

@app.route('/Digital-Ticket')
def digital_ticket():
    return render_template('digital-ticket.html')

if __name__ == '__main__':
    app.run(debug=True)


