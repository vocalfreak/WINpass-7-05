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
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(recipient_email, subject, body, image_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email 
        msg['Subject'] = subject 

        msg.attach(MIMEText(body, 'plain'))

        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                img_data = img.read()
                img_type = imghdr.what(img.name)
                img_name = os.path.basename(img.name)
                image = MIMEImage(img_data, _subtype=img_type)
                image.add_header('Content-Disposition', 'attachment', filename=img_name)
                msg.attach(image)


        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())

        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")

def get_email_address(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT email, name FROM user")
    users = cursor.fetchall()
    conn.close()

    recipients = []
    names = []

    for email in users:
        recipients.append(email)
    
    for name in users:
        names.append(name)

    return recipients, names


if __name__ == "__main__":
    recipients = get_email_address("winpass.db")
    subject = "Win MMU is approaching!"
    body = "this is a test email"
    image_path = r"C:\Users\chiam\Projects\WINpass-7-05\static\email.png"

    
    for recipient_tuple in recipients:
        recipient_email = recipient_tuple[0]  
        send_email(recipient_email, subject, body, image_path)
