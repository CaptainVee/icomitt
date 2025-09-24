from django.db import models
from django.conf import settings
from core_apps.common.models import TimeStampedUUIDModel
from core_apps.goals.models import Goal
from core_apps.logs.models import GoalLog

class BaseVerification(TimeStampedUUIDModel):
    goal_log = models.ForeignKey(
        GoalLog, on_delete=models.CASCADE
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    class Meta:
        abstract = True


class TextVerification(BaseVerification):
    goal_log = models.ForeignKey(
        GoalLog, on_delete=models.CASCADE, related_name="text_verifications"
    )
    content = models.TextField()


class PhotoVerification(BaseVerification):
    goal_log = models.ForeignKey(
        GoalLog, on_delete=models.CASCADE, related_name="image_verifications"
    )
    image = models.ImageField(upload_to="goal_proofs/photos/")


class VideoVerification(BaseVerification):
    goal_log = models.ForeignKey(
        GoalLog, on_delete=models.CASCADE, related_name="video_verifications"
    )
    video = models.FileField(upload_to="goal_proofs/videos/")


class FriendVerification(BaseVerification):
    goal_log = models.ForeignKey(
        GoalLog, on_delete=models.CASCADE, related_name="friend_verifications"
    )
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="friend_verifications",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True, null=True)



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
    goal_log = models.OneToOneField(GoalLog, on_delete=models.CASCADE, related_name="penalty")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, default="Missed goal")
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Penalty {self.amount} for {self.goal_log}"