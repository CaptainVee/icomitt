from django.db import models
from core_apps.goals.models import Goal
from core_apps.common.models import TimeStampedUUIDModel

# Create your models here.

class GoalLog(TimeStampedUUIDModel):
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
