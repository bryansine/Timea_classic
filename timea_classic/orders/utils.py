# orders/utils.py

from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

def send_order_confirmation_email(order, request=None):
    """
    Generates the order verification/receipt link and emails the order confirmation.
    """
    receipt_path = reverse('orders:order_receipt', kwargs={'order_id': order.id})
    
    if request:
        receipt_url = request.build_absolute_uri(receipt_path)
    else:
        domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
        receipt_url = f"{protocol}://{domain}{receipt_path}"

    subject = f"Order Confirmation - #{order.id}"
    
    message = (
        f"Hi {order.first_name or 'Valued Customer'},\n\n"
        f"Your payment for Order #{order.id} was received successfully!\n\n"
        f"You can view your receipt and track your order status anytime using this link:\n"
        f"{receipt_url}\n\n"
        f"Thank you for shopping with us!"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=True,
    )