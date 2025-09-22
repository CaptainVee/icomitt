import datetime

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
