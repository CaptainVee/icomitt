from rest_framework import serializers
from .models import Wallet, WalletTransaction, PayoutRequest


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "balance", "staked_balance"]

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ["id", "reference", "amount", "type", "status", "created_at"]


class FundWalletSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=100,  # ensure it's > 100
    )


class PayoutRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        fields = ["id", "amount", "bank_code", "account_number"]

    def validate_amount(self, value):
        if value <= 1000:
            raise serializers.ValidationError("Amount must be greater than 1000.")
        return value
