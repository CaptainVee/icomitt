
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)




def send_verification_email(email, code, code_type):
    """
    Send verification email with 6-digit code
    """
    try:
        if code_type == 'registration':
            subject = 'Verify Your Account'
            message = f'Your verification code is: {code}\n\nThis code will expire in 15 minutes.'
            html_message = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Welcome! Please verify your account</h2>
                <p>Your verification code is:</p>
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 2px; border-radius: 5px; margin: 20px 0;">
                    {code}
                </div>
                <p>This code will expire in 15 minutes.</p>
                <p>If you didn't request this verification, please ignore this email.</p>
            </div>
            '''
        elif code_type == 'password_reset':
            subject = 'Reset Your Password'
            message = f'Your password reset code is: {code}\n\nThis code will expire in 15 minutes.'
            html_message = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Password Reset Request</h2>
                <p>Your password reset code is:</p>
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 2px; border-radius: 5px; margin: 20px 0;">
                    {code}
                </div>
                <p>This code will expire in 15 minutes.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
            </div>
            '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email after successful registration
    """
    try:
        subject = 'Welcome to Our Platform!'
        message = f'Hello {user.username},\n\nWelcome to our platform! Your account has been successfully verified.'
        html_message = f'''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome {user.username}!</h2>
            <p>Your account has been successfully verified and is now active.</p>
            <p>You can now login and start using our platform.</p>
            <p>Thank you for joining us!</p>
        </div>
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False