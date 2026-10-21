from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_frontend_url(path):
    return settings.FRONTEND_URL.rstrip("/") + path


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = build_frontend_url(f"/verify-email?uid={uid}&token={token}")
    send_mail(
        "Verify your SCOTT student account",
        f"Welcome to SCOTT. Verify your email by opening this link: {link}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = build_frontend_url(f"/reset-password?uid={uid}&token={token}")
    send_mail(
        "Reset your SCOTT password",
        f"Reset your SCOTT password using this link: {link}\n\nThis link expires when your password changes.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
