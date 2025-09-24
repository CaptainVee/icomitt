from django.urls import path
from .views import WalletView, FundWalletView, VerifyPaymentView, StakeFundsView

urlpatterns = [
    path("", WalletView.as_view(), name="wallet"),
    path("fund/", FundWalletView.as_view(), name="wallet-fund"),
    path("verify/", VerifyPaymentView.as_view(), name="wallet-verify"),
    path("stake/", StakeFundsView.as_view(), name="wallet-stake"),
]
