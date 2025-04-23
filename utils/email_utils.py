import smtplib 
import getpass

HOST = "smtp-mail.outlook.com"
PORT = 587

FROM_EMAIL = "vocalfreak525@gmail.com"
TO_EMAIL = "vocalfreak525@outlook.com"
PASSWORD = getpass.getpass("Enter your password: ")

MESSAGE = """Subject: Mail sent using python 
Hi bitch,

This email is sent using python's smtplib and getpass module. 

Thanks,
Chiam Juin Hoong"""

smtp = smtplib.SMTP(HOST, PORT)

status_code, response = smtp.ehlo()
print(f"[*] Starting TLS connection: {status_code} {response}")

status_code, response * smtp.login(FROM_EMAIL, PASSWORD)
print(f"[*] Loggin in: {status_code} {response}")

smtp.sendmail(FROM_EMAIL, TO_EMAIL, MESSAGE)
smtp.quit()
