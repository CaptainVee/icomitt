from django.urls import path

from .views import (
    RegisterView, VerifyEmailView, LoginView, PasswordResetRequestView, PasswordResetConfirmView,
    ResendVerificationCodeView, UserProfileView)

app_name = 'users'


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('resend-verification/', ResendVerificationCodeView.as_view(), name='resend_verification'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
