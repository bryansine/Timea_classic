# orders/signals.py

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.core import signing
from .models import Order

@receiver(post_save, sender=Order)
def send_order_status_update_email(sender, instance, created, **kwargs):
    status_changed = instance.tracker.has_changed('status') if hasattr(instance, 'tracker') else True

    if created or status_changed:
        token = signing.dumps({'order_id': instance.id})
        tracking_url = f"{settings.SITE_URL}{reverse('orders:order_receipt', args=[instance.id])}?token={token}"
        
        subject = f"Order #{instance.id} Status Update: {instance.get_status_display()}"
        message = f"Hi {instance.first_name},\n\nYour order status for Order #{instance.id} at Timea Classic has been updated to: {instance.get_status_display().upper()}\n\nTrack your order anytime here:\n{tracking_url}\n\nThank you!\nTimea Classic Team"

        def send():
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
                print(f"[SIGNAL] Tracking email successfully sent to {instance.email} for Order #{instance.id}")
            except Exception as e:
                print(f"[SIGNAL ERROR] Failed to send status email: {e}")

        # Defers email sending until after the database commit completes
        transaction.on_commit(send)