from django.test import TestCase

# Create your tests here.

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