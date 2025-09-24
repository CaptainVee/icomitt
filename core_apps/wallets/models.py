from django.conf import settings
from django.db import models
from core_apps.common.models import TimeStampedUUIDModel
from decimal import Decimal
from core_apps.logs.models import GoalLog

User = settings.AUTH_USER_MODEL


class Wallet(TimeStampedUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    staked_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email} - {self.balance}"

    def credit(self, amount: Decimal):
        self.balance += amount
        self.save(update_fields=["balance"])

    def debit(self, amount: Decimal):
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save(update_fields=["balance"])


class WalletTransaction(TimeStampedUUIDModel):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    TRANSACTION_STATUS = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]

    DEPOSIT = "deposit"
    STAKE = "stake"

    TRANSACTION_TYPE = [
        (DEPOSIT, "Deposit"),
        (STAKE, "Stake"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default=PENDING)

    def __str__(self):
        return f"{self.wallet.user.email} - {self.type} - {self.amount} - {self.status}"


class PayoutRequest(TimeStampedUUIDModel):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=100, blank=True)  # filled after verification
    recipient_code = models.CharField(max_length=100, blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} ({self.status})"
