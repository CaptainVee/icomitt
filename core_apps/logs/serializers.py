from rest_framework import serializers
from .models import GoalLog
from core_apps.goals.serializers import GoalSerializer
from core_apps.verifications.serializers import PenaltySerializer

class GoalLogListSerializer(serializers.ModelSerializer):
    goal_title = serializers.CharField(source="goal.title", read_only=True)

    class Meta:
        model = GoalLog
        fields = ["id", "goal", "goal_title", "date", "status", "penalty_applied"]


class GoalLogDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with goal + penalties"""
    goal = GoalSerializer(read_only=True)
    penalties = PenaltySerializer(many=True, read_only=True)

    class Meta:
        model = GoalLog
        fields = ["id", "goal", "date", "status", "completed_at", "penalties"]