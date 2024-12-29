# core/management/commands/create_user_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = "Creates UserProfile for users who don't have one"

    def handle(self, *args, **kwargs):
        users = User.objects.all()

        for user in users:
            try:
                user.userprofile
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'UserProfile created for user: {user.username}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'UserProfile already exists for user: {user.username}'))