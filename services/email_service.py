def send_admin_order_email(order_number: str, total_amount: float):
    if not SMTP_PASSWORD:
        return  # silently skip if not configured
        
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
    except Exception:
        pass  # silently ignore errors
