from django.utils import timezone
from goals.models import Goal
from core_apps.logs.models import GoalLog
from core_apps.verifications.models import Penalty
from core_apps.goals.service import GoalEvaluator

def evaluate_goals():
    today = timezone.now().date()
    goals = Goal.objects.filter(is_active=True, is_completed=False)

    for goal in goals:
        evaluator = GoalEvaluator(goal)

        if evaluator.is_due_today():
            # If not completed, mark missed
            if not evaluator.already_completed_today():
                if not evaluator.already_logged_today():
                    log = GoalLog.objects.create(
                        goal=goal,
                        date=today,
                        status="missed",
                        penalty_applied=False,
                    )
                    if goal.penalty_amount > 0:
                        Penalty.objects.create(
                            goal_log=log,
                            amount=goal.penalty_amount,
                            reason="Missed goal"
                        )
                        log.penalty_applied = True
                        log.save()
