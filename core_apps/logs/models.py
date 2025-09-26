from django.db import models
from core_apps.goals.models import Goal
from core_apps.common.models import TimeStampedUUIDModel


class GoalLog(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("completed", "Completed"),
        ("missed", "Missed"),
        ("excused", "Excused"),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    penalty_applied = models.BooleanField(default=False)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Optional fields for tracking
    notes = models.TextField(blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ("goal", "date")
        ordering = ["-date"]
    #TODO change this to divide the total amount to multiple of the days
    def save(self, *args, **kwargs):
        # Set penalty amount from goal if not set
        if self.penalty_amount is None:
            self.penalty_amount = self.goal.penalty_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.goal.title} - {self.date} ({self.status})"

