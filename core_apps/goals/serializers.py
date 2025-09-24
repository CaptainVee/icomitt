from rest_framework import serializers
from .models import Goal
from core_apps.verifications.serializers import HumanVerifierSerializer
from core_apps.verifications.models import HumanVerifier


class GoalSerializer(serializers.ModelSerializer):
    human_verifiers = HumanVerifierSerializer(many=True, required=False)
    
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'frequency', 'time_of_day', 'duration_minutes', 'weekdays',
            'specific_dates', 'target_count', 'penalty_amount', 'payment_method',
            'verification_method', 'verification_type', 'human_verifiers'
        ]
    
    def create(self, validated_data):
        human_verifiers_data = validated_data.pop('human_verifiers', [])
        goal = Goal.objects.create(**validated_data)
        
        for verifier_data in human_verifiers_data:
            HumanVerifier.objects.create(goal=goal, **verifier_data)
        
        return goal


class GoalBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'frequency', 'time_of_day', 'duration_minutes', 
            'weekdays', 'specific_dates', 'target_count'
        ]


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


class GoalStakeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['penalty_amount', 'payment_method']


class GoalVerificationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['verification_type', 'verification_method']


class GoalHumanVerifierInfoSerializer(serializers.Serializer):
    human_verifiers = HumanVerifierSerializer(many=True)



# class GoalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Goal
#         fields = "__all__"
#         read_only_fields = ("user", "created_at", "updated_at")

#     def validate(self, data):
#         freq = data.get("frequency")

#         if freq == "daily":
#             if not data.get("duration_minutes"):
#                 raise serializers.ValidationError("Daily goals must have a duration.")
        
#         if freq == "weekly":
#             if not data.get("weekdays") and not data.get("target_count"):
#                 raise serializers.ValidationError(
#                     "Weekly goals must specify weekdays or target_count."
#                 )

#         if freq == "specific_days":
#             if not data.get("specific_dates"):
#                 raise serializers.ValidationError("Specific days goals require dates.")

#         return data