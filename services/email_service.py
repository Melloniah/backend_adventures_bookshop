def send_order_confirmation(email: str, order_number: str):
    print(f"Sending order confirmation to {email} for order {order_number}")

def send_admin_order_notification(order_number: str, total_amount: float):
    print(f"Sending admin notification for order {order_number}, amount: {total_amount}")

