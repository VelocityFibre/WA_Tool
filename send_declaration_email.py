#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
sender_email = "ai@velocityfibre.co.za"
receiver_email = "ai@velocityfibre.co.za"
subject = "Powerful Daily Declaration"

# Create message
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject

# Declaration text
body = """I have a powerful declaration for you that can transform your day into purpose, fill it with an atmosphere of power, and arm you with a victorious spirit. Would you like to receive it?"""

msg.attach(MIMEText(body, 'plain'))

# Send email (using local SMTP server)
try:
    server = smtplib.SMTP('localhost')
    server.send_message(msg)
    server.quit()
    print(f'Success: Email sent to {receiver_email}')
except Exception as e:
    print(f'Error sending email: {str(e)}')
