import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core_apps.goals.models import Goal

User = get_user_model()

class Command(BaseCommand):
    help = "Populate the database with 10 sample goals spread across 3 users."

    def handle(self, *args, **kwargs):
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Run create_users first."))
            return

        titles = [
            "Morning Jog",
            "Read a Book",
            "Drink Water",
            "Practice Coding",
            "Meditation",
            "Write Journal",
            "Daily Prayer",
            "Learn Django",
            "Plan Next Day",
            "Call Parents",
        ]

        verification_methods = ["text", "photo", "video", "friend"]
        verification_types = ["ai", "human"]
        payment_methods = ["wallet", "credit_card"]
        frequencies = ["daily", "weekly", "specific_days", "count_based"]

        for i, title in enumerate(titles):
            user = random.choice(users)
            goal = Goal.objects.create(
                user=user,
                title=title,
                description=f"Auto generated goal {i+1}",
                start_date=timezone.now().date(),
                end_date=None,
                frequency=random.choice(frequencies),
                time_of_day=None,
                duration_minutes=random.choice([15, 30, 45, 60]),
                weekdays=random.choice([["monday"], ["tuesday","thursday"], None]),
                specific_dates=None,
                target_count=random.choice([None, 2, 3]),
                penalty_amount=random.randint(5, 50),
                payment_method=random.choice(payment_methods),
                is_active=True,
                is_completed=False,
                verification_method=random.choice(verification_methods),
                verification_type=random.choice(verification_types),
            )
            self.stdout.write(self.style.SUCCESS(f"Goal '{goal.title}' created for {user.username}"))
