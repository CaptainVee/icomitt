from rest_framework import serializers
from .models import Goal, GoalLog, Penalty

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = "__all__"
        read_only_fields = ("user", "created_at", "updated_at")

    def validate(self, data):
        freq = data.get("frequency")

        if freq == "daily":
            if not data.get("duration_minutes"):
                raise serializers.ValidationError("Daily goals must have a duration.")
        
        if freq == "weekly":
            if not data.get("weekdays") and not data.get("target_count"):
                raise serializers.ValidationError(
                    "Weekly goals must specify weekdays or target_count."
                )

        if freq == "specific_days":
            if not data.get("specific_dates"):
                raise serializers.ValidationError("Specific days goals require dates.")

        return data


class GoalLogSerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source="goal.title", read_only=True)

    class Meta:
        model = GoalLog
        fields = ["id", "goal", "goal_title", "date", "status", "penalty_applied"]
