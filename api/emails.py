"""Transactional email helpers for account lifecycle events.

All links point at the frontend (settings.FRONTEND_URL); the frontend
pages call back into the API to complete each action.
"""
from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

EMAIL_VERIFY_SALT = 'devlaunch:email-verify'
# 24h to confirm an address.
EMAIL_VERIFY_MAX_AGE = 60 * 60 * 24


def make_email_verification_token(user):
    return signing.dumps({'user_id': user.pk}, salt=EMAIL_VERIFY_SALT)


def read_email_verification_token(token):
    """Return the user id encoded in a verification token, or None."""
    try:
        data = signing.loads(
            token, salt=EMAIL_VERIFY_SALT, max_age=EMAIL_VERIFY_MAX_AGE
        )
    except signing.BadSignature:
        return None
    return data.get('user_id')


def _frontend_url(path):
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}"


def send_welcome_email(user):
    send_mail(
        subject='Welcome to DevLaunch',
        message=(
            f"Hi {user.full_name},\n\n"
            "Your DevLaunch account is ready. Pick a template, customise it, "
            "and launch your site from a single dashboard.\n\n"
            "— The DevLaunch team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_verification_email(user):
    token = make_email_verification_token(user)
    link = _frontend_url(f"/verify-email?token={token}")
    send_mail(
        subject='Confirm your DevLaunch email',
        message=(
            f"Hi {user.full_name},\n\n"
            "Confirm your email address to activate your DevLaunch account:\n\n"
            f"{link}\n\n"
            "This link expires in 24 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = _frontend_url(f"/reset-password?uid={uid}&token={token}")
    send_mail(
        subject='Reset your DevLaunch password',
        message=(
            f"Hi {user.full_name},\n\n"
            "We received a request to reset your DevLaunch password. "
            "If this was you, choose a new password here:\n\n"
            f"{link}\n\n"
            "This link expires in 30 minutes. If you didn't ask for this, "
            "you can ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
