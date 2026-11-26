import smtplib
from email.mime.text import MIMEText

def send_reset_email(receiver_email, token):
    # حطي الإيميل ديالك هنا إلا بغيتي، ولكن دابا خليه هكذا باش ما يبانش فـ GitHub
    SENDER_EMAIL = "" 
    SENDER_PASSWORD = "" 
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print(f"--- TESTING ONLY --- Reset Token for {receiver_email}: {token}")
        return False # كيرجع False باش الكود يعرف بلي ماصيفطش الإيميل
    
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