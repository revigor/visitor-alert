import smtplib
from email.mime.text import MIMEText

# Email parameters
SMTP_SERVER = 'mail.smtp2go.com'
SMTP_PORT = 587
SENDER_EMAIL = 'jorge.prado@royalexpressinc.com'
SMTP_USERNAME = 'royalexpressinc.com'
SMTP_PASSWORD = 'j6oguMXuuBCiCTLH'

# Create email
recipient_email = 'revigor5@gmail.com'
msg = MIMEText("Test email from PythonAnywhere.")
msg['Subject'] = "Test Email"
msg['From'] = SENDER_EMAIL
msg['To'] = recipient_email

# Send email
try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()  # Start TLS encryption
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
    print("Email sent successfully.")
except Exception as e:
    print(f"Error sending email: {e}")
