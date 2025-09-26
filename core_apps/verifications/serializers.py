from .models import HumanVerifier, Penalty
from rest_framework import serializers
from datetime import date
from core_apps.goals.models import Goal


class HumanVerifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanVerifier
        fields = ['contact_type', 'contact_value', 'name']
        
    def validate(self, data):
        contact_type = data.get("contact_type")
        contact_value = data.get("contact_value")

        if contact_type == 'email':
            if '@' not in contact_value:
                raise serializers.ValidationError({"contact_value": "Invalid email format"})
        elif contact_type == 'whatsapp':
            normalized = contact_value.replace('+', '').replace('-', '').replace(' ', '')
            if not normalized.isdigit():
                raise serializers.ValidationError({"contact_value": "Invalid phone number format"})

        return data
    

class PenaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = Penalty
        fields = ["id", "type", "amount", "reason", "applied_at"]