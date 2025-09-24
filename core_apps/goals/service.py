import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import TextVerification, FriendVerification, PhotoVerification, VideoVerification, Penalty

class GoalEvaluator:
    def __init__(self, goal):
        self.goal = goal
        self.today = datetime.date.today()
        self.weekday = self.today.strftime("%A").lower()  # e.g. "monday"

    def is_due_today(self):
        """Check if the goal should be attempted today"""
        if not self.goal.is_active or self.goal.is_completed:
            return False

        if self.goal.frequency == "daily":
            return True

        if self.goal.frequency == "weekly":
            return self.goal.days_of_week and self.weekday in self.goal.days_of_week

        if self.goal.frequency == "custom_dates":
            return str(self.today) in (self.goal.custom_dates or [])

        if self.goal.frequency == "n-per-week":
            return self._is_due_n_per_week()

        return False

    def _is_due_n_per_week(self):
        """Check if user still has remaining attempts this week"""
        start_of_week = self.today - datetime.timedelta(days=self.today.weekday())
        logs = self.goal.logs.filter(date__gte=start_of_week, date__lte=self.today)

        completed_count = logs.filter(status="completed").count()
        return completed_count < (self.goal.times_per_week or 0)

    def already_completed_today(self):
        return self.goal.logs.filter(date=self.today, status="completed").exists()

    def already_logged_today(self):
        return self.goal.logs.filter(date=self.today).exists()


class GoalLogService:

    @staticmethod
    def submit_proof(goal_log, user, proof_type, data):
        goal = goal_log.goal

        # ✅ ensure proof type matches required type
        if proof_type != goal.verification_method:
            raise ValidationError(
                f"This goal requires {goal.get_verification_method_display()} proof."
            )

        # ✅ create verification object
        if proof_type == "text":
            proof = TextVerification.objects.create(goal_log=goal_log, content=data["content"])
            proof.verified = True  # auto-verify
            proof.save()

        elif proof_type == "photo":
            proof = PhotoVerification.objects.create(goal_log=goal_log, image=data["file"])
            # maybe auto-verify or leave for manual review

        elif proof_type == "video":
            proof = VideoVerification.objects.create(goal_log=goal_log, video=data["file"])
            # maybe auto-verify or leave for manual review

        elif proof_type == "friend":
            proof = FriendVerification.objects.create(
                goal_log=goal_log,
                verifier=data["verifier"],
                message=data.get("message", "")
            )
            # pending until friend approves

        # ✅ update log status
        GoalLogService.evaluate_status(goal_log)

        return proof

    @staticmethod
    def evaluate_status(goal_log):
        """
        Check all verifications and decide if log is completed or missed.
        """
        verifications = goal_log.verifications.all()

        if any(v.verified for v in verifications):
            goal_log.status = "completed"
            goal_log.penalty_applied = False
        else:
            # if deadline passed and still no verification
            if goal_log.date < timezone.now().date():
                goal_log.status = "missed"
                # create penalty if not already applied
                if not goal_log.penalty_applied:
                    Penalty.objects.create(
                        goal_log=goal_log,
                        amount=goal_log.goal.penalty_amount,
                        reason="Missed without valid proof"
                    )
                    goal_log.penalty_applied = True
        goal_log.save()
