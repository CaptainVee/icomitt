from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from .utils import send_verification_email
from .models import EmailVerificationCode
from core_apps.common.mixins import StandardResponseMixin
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    EmailVerificationSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



class RegisterView(StandardResponseMixin, GenericAPIView):
    """
    User registration endpoint.
    Creates inactive user and sends verification email.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer, error_response = self.validate_serializer(
            UserRegistrationSerializer, 
            request.data
        )
        if error_response:
            return error_response

        user = serializer.save()
        return self.success_response(
            data={"email": user.email},
            message="Registration successful. Please check your email for verification code.",
            status_code=status.HTTP_201_CREATED
        )

class LoginView(StandardResponseMixin, GenericAPIView):
    """
    User login endpoint.
    Returns JWT tokens for active users, sends new verification for inactive users.
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer, error_response = self.validate_serializer(
            UserLoginSerializer, 
            request.data
        )
        if error_response:
            return error_response

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data
        
        return self.success_response(
            data={
                "user": user_data,
                "tokens": tokens
            },
            message="Login successful."
        )

class VerifyEmailView(StandardResponseMixin, GenericAPIView):
    """
    Email verification endpoint.
    Activates user account and returns JWT tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer, error_response = self.validate_serializer(
            EmailVerificationSerializer, 
            request.data
        )
        if error_response:
            return error_response

        user = serializer.validated_data['user']
        verification_code = serializer.validated_data['verification_code']
        
        # Activate user and mark code as used
        user.is_active = True
        user.save()
        verification_code.is_used = True
        verification_code.save()
        
        # Generate tokens and user data
        tokens = get_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data
        
        return self.success_response(
            data={
                "user": user_data,
                "tokens": tokens
            },
            message="Email verified successfully."
        )





class PasswordResetRequestView(StandardResponseMixin, GenericAPIView):
    """
    Password reset request endpoint.
    Sends 6-digit code to user's email.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer, error_response = self.validate_serializer(
            PasswordResetRequestSerializer, 
            request.data
        )
        if error_response:
            return error_response

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create password reset code
        verification_code = EmailVerificationCode.objects.create(
            user=user,
            code_type='password_reset'
        )
        send_verification_email(email, verification_code.code, 'password_reset')
        
        return self.success_response(
            message="Password reset code sent to your email."
        )


class PasswordResetConfirmView(StandardResponseMixin, GenericAPIView):
    """
    Password reset confirmation endpoint.
    Verifies code and updates user password.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer, error_response = self.validate_serializer(
            PasswordResetConfirmSerializer, 
            request.data
        )
        if error_response:
            return error_response

        user = serializer.validated_data['user']
        verification_code = serializer.validated_data['verification_code']
        new_password = serializer.validated_data['new_password']
        
        # Update password and mark code as used
        user.set_password(new_password)
        user.save()
        verification_code.is_used = True
        verification_code.save()
        
        return self.success_response(
            message="Password reset successfully."
        )


class ResendVerificationCodeView(StandardResponseMixin, GenericAPIView):
    """
    Resend verification code endpoint.
    Sends new verification code to inactive users.
    """
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return self.error_response("Email is required.")
        
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return self.error_response("Account is already verified.")
            
            # Create new verification code
            verification_code = EmailVerificationCode.objects.create(
                user=user,
                code_type='registration'
            )
            send_verification_email(email, verification_code.code, 'registration')
            
            return self.success_response(
                message="New verification code sent to your email."
            )
        except User.DoesNotExist:
            return self.error_response(
                "User not found.", 
                status_code=status.HTTP_404_NOT_FOUND
            )


class UserProfileView(StandardResponseMixin, GenericAPIView):
    """
    User profile endpoint.
    Returns authenticated user's profile information.
    """
    serializer_class = UserProfileSerializer

    def get(self, request):
        user_data = UserProfileSerializer(request.user).data
        return self.success_response(
            data=user_data,
            message="Profile retrieved successfully."
        )
