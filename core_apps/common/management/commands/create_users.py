# core_apps/common/management/commands/create_users.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = "Populate the database with 3 users (1 superadmin and 2 regular users)."

    def handle(self, *args, **kwargs):
        # Superuser
        if not User.objects.filter(username=settings.ADMIN_USERNAME).exists():
            User.objects.create_superuser(
                username=settings.ADMIN_USERNAME,
                email=settings.EMAIL,
                password=settings.PASSWORD,
                first_name="Super",
                last_name="Admin",
                date_joined=timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS("Superadmin created."))
        else:
            self.stdout.write(self.style.WARNING("Superadmin already exists."))

        # Regular users
        users_data = [
            {"username": "makozi", "email": "makozi.dev@gmail.com", "password": "password321"},
            {"username": "user1", "email": "user1@example.com", "password": "password321"},
        ]

        for data in users_data:
            if not User.objects.filter(username=data["username"]).exists():
                User.objects.create_user(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"],
                    first_name=data["username"].capitalize(),
                    last_name="Test",
                    date_joined=timezone.now(),
                )
                self.stdout.write(self.style.SUCCESS(f"User {data['username']} created."))
            else:
                self.stdout.write(self.style.WARNING(f"User {data['username']} already exists."))
