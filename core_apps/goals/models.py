from django.db import models
from django.conf import settings
from django.utils import timezone
from core_apps.common.models import TimeStampedUUIDModel
# from django.contrib.postgres.fields import ArrayField


class Goal(TimeStampedUUIDModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="goals"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    frequency = models.CharField(
        max_length=20, 
        choices=[("daily","Daily"), ("weekly","Weekly"), 
                 ("specific_days","Specific Days"), ("count_based","Count Based")]
    )
    time_of_day = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    weekdays = models.CharField(models.CharField(max_length=9), null=True, blank=True)  # e.g. ["sunday","wednesday"]
    # weekdays = ArrayField(models.CharField(max_length=9), null=True, blank=True)  # e.g. ["sunday","wednesday"]
    specific_dates = models.CharField(models.DateField(), null=True, blank=True)  # e.g. ["2025-10-04", "2025-10-10"]
    # specific_dates = ArrayField(models.DateField(), null=True, blank=True)  # e.g. ["2025-10-04", "2025-10-10"]
    target_count = models.PositiveIntegerField(null=True, blank=True)  # e.g. 2 per week

    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)   # soft deactivate goal
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.user})"


class GoalLog(models.Model):
    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("missed", "Missed"),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    penalty_applied = models.BooleanField(default=False)

    class Meta:
        unique_together = ("goal", "date")

    def __str__(self):
        return f"{self.goal.title} - {self.date} ({self.status})"


class Penalty(models.Model):
    goal_log = models.OneToOneField(GoalLog, on_delete=models.CASCADE, related_name="penalty")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, default="Missed goal")
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Penalty {self.amount} for {self.goal_log}"





# # models.py
# from django.db import models
# from django.contrib.auth.models import User
# from django.utils import timezone
# from datetime import datetime, timedelta


# class Goal(models.Model):
#     STATUS_CHOICES = [
#         ('active', 'Active'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed'),
#     ]

#     RECURRENCE_CHOICES = [
#         ('none', 'None'),
#         ('daily', 'Daily'),
#         ('weekly', 'Weekly'),
#         ('monthly', 'Monthly'),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
#     title = models.CharField(max_length=255)
#     description = models.TextField(blank=True)

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

#     # Dates
#     due_date = models.DateField(null=True, blank=True)
#     due_time = models.TimeField(null=True, blank=True)
#     due_datetime = models.DateTimeField(null=True, blank=True)

#     # Recurrence
#     recurrence_type = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default="none")
#     recurrence_interval = models.PositiveIntegerField(default=1)  # every X days/weeks/months
#     recurrence_end_date = models.DateField(null=True, blank=True)

#     # Metadata
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     next_due_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         ordering = ["next_due_at", "due_datetime", "due_date"]

#     def __str__(self):
#         return f"{self.title} ({self.user.username})"

#     def save(self, *args, **kwargs):
#         # Ensure we always have a unified due datetime
#         if not self.due_datetime and self.due_date:
#             if self.due_time:
#                 self.due_datetime = datetime.combine(self.due_date, self.due_time)
#             else:
#                 self.due_datetime = datetime.combine(self.due_date, datetime.min.time())
#         self.calculate_next_due()
#         super().save(*args, **kwargs)

#     def calculate_next_due(self):
#         """Compute next due date based on recurrence."""
#         if self.recurrence_type == "none":
#             self.next_due_at = self.due_datetime
#             return

#         if not self.due_datetime:
#             return

#         current_due = self.due_datetime
#         now = timezone.now()

#         if self.recurrence_type == "daily":
#             while current_due <= now:
#                 current_due += timedelta(days=self.recurrence_interval)

#         elif self.recurrence_type == "weekly":
#             while current_due <= now:
#                 current_due += timedelta(weeks=self.recurrence_interval)

#         elif self.recurrence_type == "monthly":
#             # Naive monthly increment: +30 days
#             while current_due <= now:
#                 current_due += timedelta(days=30 * self.recurrence_interval)

#         # Respect recurrence end date if provided
#         if self.recurrence_end_date and current_due.date() > self.recurrence_end_date:
#             self.next_due_at = None
#         else:
#             self.next_due_at = current_due

#     @property
#     def is_overdue(self):
#         if not self.next_due_at:
#             return False
#         return timezone.now() > self.next_due_at

#     @property
#     def time_until_due(self):
#         if not self.next_due_at:
#             return None
#         return self.next_due_at - timezone.now()
