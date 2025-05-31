import smtplib 
import os 
import imghdr
from email.mime.text import MIMEText 
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart 
from dotenv import load_dotenv 
import sqlite3

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "vocalfreak525@gmail.com"
EMAIL_PASSWORD = "frmu enzt celh dpvj"

def send_email(subject, body, image_path, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT email, nonce FROM user")
    users = cursor.fetchall()
    conn.close()

    #html_template_path = r'C:\Users\chiam\Projects\WINpass-7-05\templates\email.html'
    html_template_path = r'C:\Mini IT\WINpass-7-05\templates\email.html'
    with open(html_template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    for (recipient_email, nonce) in users:
        try:
            pre_registration_url = f"http://127.0.0.1:5000/Pre_Registration_page?token={nonce}"
            html_content = html_template.replace("{{pre_registration_link}}", pre_registration_url)
            msg = MIMEMultipart('related')
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(html_content, 'html'))

            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as img:
                    img_data = img.read()
                    img_type = imghdr.what(img.name)
                    img_name = os.path.basename(img.name)
                    image = MIMEImage(img_data, _subtype=img_type)
                    image.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=img_name
                    )
                    msg.attach(image)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(
                    EMAIL_ADDRESS,
                    recipient_email,
                    msg.as_string()
                )
        except Exception as e:
            print(f"Error sending to {recipient_email}: {e}")



