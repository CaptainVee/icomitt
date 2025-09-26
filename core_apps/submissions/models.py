from django.db import models
from django.utils import timezone
from core_apps.common.models import TimeStampedUUIDModel
from core_apps.logs.models import GoalLog
from core_apps.verifications.models import HumanVerifier


class Submission(TimeStampedUUIDModel):
    """Base submission model for all types of verification submissions"""
    SUBMISSION_STATUS = [
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    goal_log = models.OneToOneField(
        GoalLog, 
        on_delete=models.CASCADE, 
        related_name="submission"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=SUBMISSION_STATUS, default="submitted")
    
    # AI/Human verification fields
    verified_by = models.ForeignKey(
        HumanVerifier, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="verified_submissions"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # AI confidence score (0-1)
    ai_confidence_score = models.FloatField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Update goal_log status based on submission status
        if self.status == "approved":
            self.goal_log.status = "completed"
            self.goal_log.completion_time = self.verified_at or timezone.now()
            self.goal_log.save()
        elif self.status == "rejected":
            self.goal_log.status = "missed"
            self.goal_log.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Submission for {self.goal_log}"


class TextSubmission(models.Model):
    """Text-based verification submission"""
    submission = models.OneToOneField(
        Submission, 
        on_delete=models.CASCADE, 
        related_name="text_content"
    )
    content = models.TextField()

    def __str__(self):
        return f"Text: {self.content[:50]}..."


class PhotoSubmission(models.Model):
    """Photo-based verification submission"""
    submission = models.OneToOneField(
        Submission, 
        on_delete=models.CASCADE, 
        related_name="photo_content"
    )
    image = models.ImageField(upload_to='goal_submissions/photos/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Photo: {self.image.name}"


class VideoSubmission(models.Model):
    """Video-based verification submission"""
    submission = models.OneToOneField(
        Submission, 
        on_delete=models.CASCADE, 
        related_name="video_content"
    )
    video = models.FileField(upload_to='goal_submissions/videos/')
    caption = models.CharField(max_length=255, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Video: {self.video.name}"
    







# class FriendSubmission(models.Model):
#     """Friend verification submission"""
#     submission = models.OneToOneField(
#         Submission, 
#         on_delete=models.CASCADE, 
#         related_name="friend_content"
#     )
#     friend_email = models.EmailField()
#     friend_name = models.CharField(max_length=100)
#     verification_code = models.CharField(max_length=6, unique=True)
#     friend_confirmed = models.BooleanField(default=False)
#     friend_confirmed_at = models.DateTimeField(null=True, blank=True)
#     message_to_friend = models.TextField(blank=True)

#     def __str__(self):
#         return f"Friend verification: {self.friend_name} ({self.friend_email})"

