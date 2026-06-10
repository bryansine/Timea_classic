from django.contrib.auth.signals import user_logged_in as django_user_logged_in
from django.dispatch import receiver
from allauth.account.signals import user_logged_in as allauth_user_logged_in
from .utils import merge_carts

# 1. This catches traditional Username/Password logins
@receiver(django_user_logged_in)
def merge_cart_on_standard_login(sender, request, user, **kwargs):
    merge_carts(request, user)

# 2. This catches modern Google OAuth logins
@receiver(allauth_user_logged_in)
def merge_cart_on_google_login(request, user, **kwargs):
    merge_carts(request, user)