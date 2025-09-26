from django.db import models
from django.conf import settings
from django.utils import timezone
from core_apps.common.models import TimeStampedUUIDModel
# from django.contrib.postgres.fields import ArrayField


class Goal(TimeStampedUUIDModel):
    SUBMISSION_METHODS = [
        ("text", "Text"),
        ("photo", "Photo"),
        ("video", "Video"),
    ]
    
    VERIFICATION_TYPES = [
        ("ai", "AI Verification"),
        ("human", "Human Verification"),
    ]
    
    PAYMENT_METHODS = [
        ("wallet", "Wallet"),
        ("credit_card", "Credit Card"),
    ]

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

    weekdays = models.JSONField(null=True, blank=True)  # e.g. ["sunday","wednesday"]
    # weekdays = ArrayField(models.CharField(max_length=9), null=True, blank=True)  # e.g. ["sunday","wednesday"]
    specific_dates = models.JSONField(null=True, blank=True)  # e.g. ["2025-10-04", "2025-10-10"]
    # specific_dates = ArrayField(models.DateField(), null=True, blank=True)  # e.g. ["2025-10-04", "2025-10-10"]
    target_count = models.PositiveIntegerField(null=True, blank=True)  # e.g. 2 per week

    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="wallet"
    )
    
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)

    submission_method = models.CharField(
        max_length=20,
        choices=SUBMISSION_METHODS,
        default="text"
    )
    verification_type = models.CharField(
        max_length=20,
        choices=VERIFICATION_TYPES,
        default="ai"
    )

    def __str__(self):
        return f"{self.title} ({self.user})"
    
