from django.db import models
from django.conf import settings
from core_apps.common.models import TimeStampedUUIDModel
from core_apps.goals.models import Goal
from core_apps.logs.models import GoalLog
from django.utils import timezone


class HumanVerifier(TimeStampedUUIDModel):
    CONTACT_TYPES = [
        ("whatsapp", "WhatsApp"),
        ("email", "Email"),
    ]
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="human_verifiers")
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    contact_value = models.CharField(max_length=255)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ("goal", "contact_type", "contact_value")

    def __str__(self):
        return f"{self.name} - {self.contact_value} for {self.goal.title}"
    

class Penalty(TimeStampedUUIDModel):
    goal_log = models.ForeignKey(
        GoalLog, 
        on_delete=models.CASCADE, 
        related_name="penalty_transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, default="Missed goal")
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Penalty {self.amount} for {self.goal_log}"
    

class Penalty(TimeStampedUUIDModel):
    """
    A generic penalty linked to a user. 
    Actual behavior depends on penalty_type and related details.
    """
    PENALTY_TYPES = [
        ("money", "Money Deduction"),
        ("email", "Send Email"),
        ("whatsapp", "Send WhatsApp"),
        ("custom", "Custom Action"),
    ]
    goal_log = models.ForeignKey(
        GoalLog, 
        on_delete=models.CASCADE, 
        related_name="penalty_transactions"
    )
    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="penalty_submission"
    )

    penalty_type = models.CharField(max_length=20, choices=PENALTY_TYPES)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    executed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("executed", "Executed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    def __str__(self):
        return f"{self.penalty_type} penalty for {self.user}"


class MoneyPenalty(models.Model):
    """
    Specific details for money penalties
    """
    penalty = models.OneToOneField(Penalty, on_delete=models.CASCADE, related_name="money_details")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    transaction_id = models.CharField(max_length=255, null=True, blank=True)  # optional link to a payment system


class ContactPenalty(models.Model):
    """
    Used for email/whatsapp penalties
    """
    penalty = models.OneToOneField(Penalty, on_delete=models.CASCADE, related_name="contact_details")
    contact_type = models.CharField(max_length=20, choices=[("email", "Email"), ("whatsapp", "WhatsApp")])
    contact_value = models.CharField(max_length=255)  # email address or phone number
    message = models.TextField()


class CustomPenalty(models.Model):
    """
    Used for custom, user-defined penalties
    """
    penalty = models.OneToOneField(Penalty, on_delete=models.CASCADE, related_name="custom_details")
    action_code = models.CharField(max_length=100)  # e.g. "tweet", "block_app", "notify_friend"
    config = models.JSONField(default=dict)  # flexible config (e.g., {"message": "Oops I failed"} )
