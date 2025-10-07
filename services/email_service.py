# services/email_service.py
import os
import smtplib
from email.mime.text import MIMEText

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "adventurersbooks@gmail.com")
FROM_EMAIL = os.getenv("FROM_EMAIL", "adventurersbooks@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "adventurersbooks@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Must be App Password for Gmail

def send_admin_order_email(order_number: str, total_amount: float):
    if not SMTP_PASSWORD:
        print("[WARNING] SMTP_PASSWORD not configured. Skipping email.")
        return
        
    subject = f"New Order Received: {order_number}"
    body = f"""
A new order has been placed.

Order Number: {order_number}
Total Amount: KSh {total_amount:,.2f}

Check the admin dashboard for details.
"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = ADMIN_EMAIL

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[INFO] Admin email sent for order {order_number}")
    except Exception as e:
        print(f"[ERROR] Failed to send admin email: {e}")