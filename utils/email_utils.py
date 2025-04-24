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

def send_email(subject, body, image_path, db_path):
    """
    Fetches all (email, name) pairs from the user table,
    personalizes the body, attaches image if provided,
    and sends one email per user.
    """
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT email, name FROM user")
    users = cursor.fetchall()
    conn.close()

    for recipient_email, name in users:
        try:
            personalized_body = f"Hi {name},\n\n{body}"

            msg = MIMEMultipart()
            msg['From']    = EMAIL_ADDRESS
            msg['To']      = recipient_email 
            msg['Subject'] = subject
            msg.attach(MIMEText(personalized_body, 'plain'))

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


