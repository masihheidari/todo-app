from datetime import timedelta

import pytest
from django.conf import settings
from django.core import mail
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken
)

from users.tasks import cleanup_expired_items, send_verification_email_task
from users.tests.factories import CustomUserFactory



def test_send_verification_email_contains_link():
    send_verification_email_task('user@example.com', 'abc123')

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == ['user@example.com']
    assert 'abc123' in sent.body
    assert settings.BACKEND_URL in sent.body



@pytest.mark.django_db
class TestCleanupExpiredItems:
    def _old_unverified_user(self, **overrides):
        user = CustomUserFactory(
            is_active=False, is_staff=False, is_superuser=False,
        )
        old_date = timezone.now() - settings.UNVERIFIED_USER_RETENTION - timedelta(days=1)
        CustomUser = user.__class__
        CustomUser.objects.filter(pk=user.pk).update(created_date=old_date)
        user.refresh_from_db()
        return user

    def test_deletes_old_unverified_user_with_no_login(self):
        user = self._old_unverified_user()

        cleanup_expired_items()

        assert not user.__class__.objects.filter(pk=user.pk).exists()

    def test_keeps_recently_created_unverified_user(self):
        user = CustomUserFactory(is_active=False)  # created_date = الان

        cleanup_expired_items()

        assert user.__class__.objects.filter(pk=user.pk).exists()

    def test_keeps_staff_user_even_if_old_and_unverified(self):
        user = self._old_unverified_user()
        user.__class__.objects.filter(pk=user.pk).update(is_staff=True)

        cleanup_expired_items()

        assert user.__class__.objects.filter(pk=user.pk).exists()

    def test_keeps_user_who_has_logged_in(self):
        user = self._old_unverified_user()
        user.__class__.objects.filter(pk=user.pk).update(last_login=timezone.now())

        cleanup_expired_items()

        assert user.__class__.objects.filter(pk=user.pk).exists()

    def test_deletes_expired_outstanding_tokens(self):
        user = CustomUserFactory()
        expired = OutstandingToken.objects.create(
            user=user, jti='expired-jti', token='x',
            created_at=timezone.now(), expires_at=timezone.now() - timedelta(days=1),
        )
        still_valid = OutstandingToken.objects.create(
            user=user, jti='valid-jti', token='y',
            created_at=timezone.now(), expires_at=timezone.now() + timedelta(days=1),
        )

        cleanup_expired_items()

        assert not OutstandingToken.objects.filter(pk=expired.pk).exists()
        assert OutstandingToken.objects.filter(pk=still_valid.pk).exists()

    def test_returns_summary_counts(self):
        self._old_unverified_user()

        result = cleanup_expired_items()

        assert result['unverified_users'] == 1
        assert result['expired_tokens'] == 0