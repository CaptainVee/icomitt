from .models import HumanVerifier, Penalty
from rest_framework import serializers


class HumanVerifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanVerifier
        fields = ['contact_type', 'contact_value', 'name']
        
    def validate_contact_value(self):
        contact_type = self.initial_data.get('contact_type')
        contact_value = self.validated_data.get('contact_value')
        
        if contact_type == 'email':
            # Basic email validation
            if '@' not in contact_value:
                raise serializers.ValidationError("Invalid email format")
        elif contact_type == 'whatsapp':
            # Basic phone number validation
            if not contact_value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise serializers.ValidationError("Invalid phone number format")
        
        return contact_value
    

class PenaltySerializer(serializers.ModelSerializer):
    class Meta:
        model = Penalty
        fields = ["id", "type", "amount", "reason", "applied_at"]