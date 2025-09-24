import requests
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.generics import GenericAPIView, RetrieveAPIView, CreateAPIView
from .models import Wallet, WalletTransaction, PayoutRequest
from .serializers import WalletSerializer, PayoutRequestSerializer, FundWalletSerializer
from core_apps.common.mixins import StandardResponseMixin
from decimal import Decimal
import uuid


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = settings.PAYSTACK_BASE_URL


class WalletView(StandardResponseMixin, RetrieveAPIView):
    """Get user wallet balance"""
    serializer_class = WalletSerializer

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class FundWalletView(StandardResponseMixin, GenericAPIView):
    """Initialize Paystack payment"""
    permission_classes = [IsAuthenticated]
    serializer_class = FundWalletSerializer

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            amount = serializer.validated_data["amount"]
            amount = request.data.get("amount")

            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            reference = str(uuid.uuid4())

            # create pending transaction
            tx = WalletTransaction.objects.create(
                wallet=wallet,
                reference=reference,
                amount=Decimal(amount),
                type=WalletTransaction.DEPOSIT,
                status=WalletTransaction.PENDING,
            )

            headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
            data = {
                "email": request.user.email,
                "amount": int(Decimal(amount) * 100),  # Paystack expects kobo
                "reference": reference,
            }

            r = requests.post(f'{PAYSTACK_BASE_URL}/transaction/initialize', json=data, headers=headers)
            res = r.json()

            if not res.get("status"):
                tx.status = WalletTransaction.FAILED
                tx.save(update_fields=["status"])
                return self.error_response("Paystack init failed", status.HTTP_400_BAD_REQUEST)

            return self.success_response(
                {"authorization_url": res["data"]["authorization_url"], "reference": reference},
                "Payment initialized",
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_400_BAD_REQUEST)

class VerifyPaymentView(StandardResponseMixin, GenericAPIView):
    """Verify Paystack payment"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return self.error_response("Reference is required", status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        r = requests.get(f'{PAYSTACK_BASE_URL}/transaction/verify/{reference}', headers=headers)
        res = r.json()

        try:
            tx = WalletTransaction.objects.get(reference=reference, wallet__user=request.user)
        except WalletTransaction.DoesNotExist:
            return self.error_response("Transaction not found", status.HTTP_404_NOT_FOUND)

        if res.get("status") and res["data"]["status"] == "success":
            tx.status = WalletTransaction.SUCCESS
            tx.save(update_fields=["status"])
            tx.wallet.credit(tx.amount)
            return self.success_response({"wallet_balance": tx.wallet.balance}, "Wallet funded")
        else:
            tx.status = WalletTransaction.FAILED
            tx.save(update_fields=["status"])
            return self.error_response("Payment failed", status.HTTP_400_BAD_REQUEST)


class StakeFundsView(StandardResponseMixin, GenericAPIView):
    """Stake funds from wallet"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        if not amount:
            return self.error_response("Amount is required", status.HTTP_400_BAD_REQUEST)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        try:
            wallet.debit(Decimal(amount))
        except ValueError as e:
            return self.error_response(str(e), status.HTTP_400_BAD_REQUEST)

        WalletTransaction.objects.create(
            wallet=wallet,
            reference=str(uuid.uuid4()),
            amount=Decimal(amount),
            type=WalletTransaction.STAKE,
            status=WalletTransaction.SUCCESS,
        )

        return self.success_response({"wallet_balance": wallet.balance}, "Funds staked")



class CreatePayoutRequestView(StandardResponseMixin, CreateAPIView):
    """User creates payout request (pending until admin approval)."""
    serializer_class = PayoutRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        payout = serializer.save(user=self.request.user)
        # Optional: immediately resolve account name for display
        r = requests.get(
            f"{PAYSTACK_BASE_URL}/bank/resolve",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
            params={
                "account_number": payout.account_number,
                "bank_code": payout.bank_code,
            },
        )
        res = r.json()
        if res.get("status"):
            payout.account_name = res["data"]["account_name"]
            payout.save()


class ApprovePayoutView(StandardResponseMixin, GenericAPIView):
    """Admin approves and triggers Paystack transfer"""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            payout = PayoutRequest.objects.get(pk=pk, status=PayoutRequest.STATUS_PENDING)
        except PayoutRequest.DoesNotExist:
            return self.error_response("Invalid payout request", 404)

        # 1. Create transfer recipient if not already stored
        if not payout.recipient_code:
            r = requests.post(
                f"{PAYSTACK_BASE_URL}/transferrecipient",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
                json={
                    "type": "nuban",
                    "name": payout.account_name or payout.user.get_full_name(),
                    "account_number": payout.account_number,
                    "bank_code": payout.bank_code,
                    "currency": "NGN",
                },
            )
            res = r.json()
            if not res.get("status"):
                return self.error_response("Failed to create transfer recipient", 400)
            payout.recipient_code = res["data"]["recipient_code"]
            payout.save()

        # 2. Initiate transfer
        r = requests.post(
            f"{PAYSTACK_BASE_URL}/transfer",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
            json={
                "source": "balance",
                "amount": int(payout.amount * 100),  # kobo
                "recipient": payout.recipient_code,
                "reason": "User payout",
            },
        )
        res = r.json()
        if res.get("status"):
            payout.status = PayoutRequest.STATUS_PAID
            payout.reference = res["data"]["reference"]
            payout.save()
            return self.success_response({"status": "paid"}, "Payout successful")

        payout.status = PayoutRequest.STATUS_FAILED
        payout.save()
        return self.error_response("Payout failed", 400)
