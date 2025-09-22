# # signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.utils import timezone
# from datetime import timedelta
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import EmailVerificationCode

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def send_signup_code(sender, instance, created, **kwargs):
#     if created and not instance.is_active:
#         code = EmailVerificationCode.generate_code()
#         EmailVerificationCode.objects.create(
#             user=instance,
#             code=code,
#             purpose="signup",
#             expires_at=timezone.now() + timedelta(minutes=10),
#         )
#         send_mail(
#             "Verify your email",
#             f"Your verification code is {code}. It expires in 10 minutes.",
#             settings.DEFAULT_FROM_EMAIL,
#             [instance.email],
#         )
