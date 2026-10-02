from unittest.mock import patch

import pytest
from rest_framework.exceptions import AuthenticationFailed

from users.api.v1.serializer import (AdminUserSerializer,
                                     ChangePasswordSerializer,
                                     CustomTokenObtainPairSerializer,
                                     RegistrationSerializer,
                                     ResendVerificationEmailSerializer)
from users.tests.factories import CustomUserFactory


@pytest.mark.django_db
class TestRegistrationSerializer:
    def _data(self, **overrides):
        """Valid registration payload; override fields to break it."""
        data = dict(
            email="ali@example.com",
            username="ali",
            password="StrongPass123",
            password1="StrongPass123",
        )
        data.update(overrides)
        return data

    def test_valid_data_passes(self):
        serializer = RegistrationSerializer(data=self._data())
        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch_fails(self):
        serializer = RegistrationSerializer(data=self._data(password1="Different123"))
        assert not serializer.is_valid()
        assert "detail" in serializer.errors

    def test_weak_password_rejected_by_django_validators(self):
        # "password123" is in Django's common-password list
        serializer = RegistrationSerializer(
            data=self._data(password="password123", password1="password123")
        )
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_duplicate_email_rejected(self):
        CustomUserFactory(email="taken@example.com")
        serializer = RegistrationSerializer(
            data=self._data(email="taken@example.com", username="other")
        )
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    # Patch where the names are used (the serializer module), not where defined.
    # Decorators apply bottom-up, so the mock args are in reverse order.
    @patch("users.api.v1.serializer.send_verification_email_task")
    @patch("users.api.v1.serializer.generate_verification_token")
    def test_create_makes_inactive_user_and_sends_email(
        self, mock_gen_token, mock_email_task
    ):
        mock_gen_token.return_value = "fake-token"
        serializer = RegistrationSerializer(data=self._data())
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user.is_active is False
        assert user.check_password("StrongPass123")
        # The email task is queued with the user's email and the token
        mock_email_task.delay.assert_called_once_with(user.email, "fake-token")


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:
    def test_active_user_logs_in_successfully(self):
        user = CustomUserFactory(is_active=True)
        serializer = CustomTokenObtainPairSerializer(
            data={"email": user.email, "password": "pass12345"}
        )
        assert serializer.is_valid(), serializer.errors
        assert "access" in serializer.validated_data

    def test_inactive_user_is_blocked_with_clear_message(self):
        user = CustomUserFactory(is_active=False)
        serializer = CustomTokenObtainPairSerializer(
            data={"email": user.email, "password": "pass12345"}
        )
        with pytest.raises(AuthenticationFailed) as exc_info:
            serializer.is_valid()
        assert "verify your email" in str(exc_info.value)

    def test_wrong_password_is_rejected(self):
        user = CustomUserFactory(is_active=True)
        serializer = CustomTokenObtainPairSerializer(
            data={"email": user.email, "password": "wrong-password"}
        )
        with pytest.raises(AuthenticationFailed):
            serializer.is_valid()


# No database needed: this serializer never touches the DB
class TestChangePasswordSerializer:
    def _data(self, **overrides):
        data = dict(
            old_password="old-anything",  # not checked here, the view does it
            new_password="StrongPass123",
            new_password1="StrongPass123",
        )
        data.update(overrides)
        return data

    def test_valid_data_passes(self):
        serializer = ChangePasswordSerializer(data=self._data())
        assert serializer.is_valid(), serializer.errors

    def test_mismatched_new_passwords_fail(self):
        serializer = ChangePasswordSerializer(
            data=self._data(new_password1="Different123")
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors

    def test_weak_new_password_fails(self):
        serializer = ChangePasswordSerializer(
            data=self._data(new_password="password123", new_password1="password123")
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors


def test_resend_verification_serializer_rejects_invalid_email():
    serializer = ResendVerificationEmailSerializer(data={"email": "not-an-email"})
    assert not serializer.is_valid()


@pytest.mark.django_db
def test_admin_serializer_ignores_readonly_fields_on_input():
    user = CustomUserFactory()
    serializer = AdminUserSerializer(
        user,
        data={"id": 999, "role": "admin", "first_name": "New"},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    # Read-only fields are dropped silently instead of raising errors
    assert "id" not in serializer.validated_data
    assert "role" not in serializer.validated_data
