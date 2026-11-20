import smtplib
from email.mime.text import MIMEText

def send_reset_email(receiver_email, token):
    # ⚠️ هنا حط الإيميل ديالك و الـ App Password ديالك
    SENDER_EMAIL = "your_email@gmail.com" 
    SENDER_PASSWORD = "xxxx xxxx xxxx xxxx" # App Password من Google
    
    subject = "Smart Closet - Password Reset Code"
    body = f"Your password reset code is: {token}\n\nThis code will expire in 15 minutes."
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False