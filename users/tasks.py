from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from users.models import CustomUser

logger = get_task_logger(__name__)


@shared_task(name="send_verification_email_task")
def send_verification_email_task(user_email: str, token: str):
    """Email the user a verification link (runs in a Celery worker)."""
    # The link points to VerifyEmailView, which looks the token up in the cache
    verification_link = (
        f"{settings.BACKEND_URL}/users/api/v1/verify-email/?token={token}"
    )

    subject = "activating your account"
    # The 15 minutes must match the cache timeout in utils.generate_verification_token
    message = (
        "in order to activate your account click here :\n"
        f"{verification_link}\n"
        "this link is valid for 15 mins."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
    )


@shared_task(name="cleanup_expired_items", ignore_result=True)
def cleanup_expired_items():
    """Periodic cleanup, scheduled by Celery Beat (see CELERY_BEAT_SCHEDULE)."""
    now = timezone.now()

    # 1) Delete JWT outstanding tokens that have already expired
    _, token_detail = OutstandingToken.objects.filter(expires_at__lte=now).delete()

    # 2) Delete accounts that were never verified within the retention period.
    # Only plain, never-used accounts match: not active, not staff/superuser,
    # never logged in, and with no related outstanding tokens left.
    cutoff = now - settings.UNVERIFIED_USER_RETENTION
    _, user_detail = CustomUser.objects.filter(
        is_active=False,
        is_staff=False,
        is_superuser=False,
        last_login__isnull=True,
        created_date__lt=cutoff,
        task__isnull=True,  # skip users that still own related tasks
    ).delete()

    # delete() returns a per-model count dict; pick out the models we care about
    result = {
        "expired_tokens": token_detail.get("token_blacklist.OutstandingToken", 0),
        "unverified_users": user_detail.get("users.CustomUser", 0),
    }
    logger.info("cleanup_expired_items done: %s", result)
    return result
