from rest_framework import serializers
from django.contrib.auth import get_user_model
# from django_countries.serializer_fields import CountryField
# from phonenumber_field.serializerfields import PhoneNumberField
from .models import EmailVerificationCode
from .utils import send_verification_email
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(is_active=False, **validated_data)
        
        # Create verification code and send email
        verification_code = EmailVerificationCode.objects.create(
            user=user,
            code_type='registration'
        )
        send_verification_email(user.email, verification_code.code, 'registration')
        
        return user



class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")

            if not user.check_password(password):
                raise serializers.ValidationError("Invalid credentials.")

            if not user.is_active:
                # Generate new verification code for inactive users
                verification_code = EmailVerificationCode.objects.create(
                    user=user,
                    code_type='registration'
                )
                send_verification_email(user.email, verification_code.code, 'registration')
                raise serializers.ValidationError("Account not verified. A new verification code has been sent to your email.")

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Email and password are required.")


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        try:
            verification_code = EmailVerificationCode.objects.get(
                user=user,
                code=code,
                code_type='registration'
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code.")

        if not verification_code.is_valid():
            raise serializers.ValidationError("Verification code has expired or been used.")

        attrs['user'] = user
        attrs['verification_code'] = verification_code
        return attrs
    


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("Account is not active.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value



class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")

        email = attrs.get('email')
        code = attrs.get('code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        try:
            verification_code = EmailVerificationCode.objects.get(
                user=user,
                code=code,
                code_type='password_reset'
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid reset code.")

        if not verification_code.is_valid():
            raise serializers.ValidationError("Reset code has expired or been used.")

        attrs['user'] = user
        attrs['verification_code'] = verification_code
        return attrs
    


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'date_joined', 'avatar_url')
        read_only_fields = ('id', 'email', 'date_joined')