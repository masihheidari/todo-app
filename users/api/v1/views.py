# users/tests/test_views.py
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.tests.factories import CustomUserFactory


@pytest.fixture
def client():
    # Overrides pytest-django's default `client` with a DRF API client
    return APIClient()


def auth(client, user):
    """Log the client in as `user` without going through the login endpoint."""
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestRegistrationView:
    url = reverse("users:api-v1:registration")

    # Mock the task and token so no real email/cache work happens
    @patch("users.api.v1.serializer.send_verification_email_task")
    @patch("users.api.v1.serializer.generate_verification_token")
    def test_register_success_creates_inactive_user(
        self, mock_token, mock_email, client
    ):
        mock_token.return_value = "tok"
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "StrongPass123",
            "password1": "StrongPass123",
        }
        response = client.post(self.url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_email.delay.assert_called_once()

    def test_register_duplicate_email_fails(self, client):
        CustomUserFactory(email="taken@example.com")
        data = {
            "email": "taken@example.com",
            "username": "someone",
            "password": "StrongPass123",
            "password1": "StrongPass123",
        }
        response = client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProfileView:
    url = reverse("users:api-v1:profile")

    def test_requires_authentication(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_own_data(self, client):
        user = CustomUserFactory(email="me@example.com")
        response = auth(client, user).get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "me@example.com"


@pytest.mark.django_db
class TestUsersListView:
    url = reverse("users:api-v1:users-list")

    def test_student_forbidden(self, client):
        student = CustomUserFactory()
        response = auth(client, student).get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_user_allowed(self, client):
        staff = CustomUserFactory(is_staff=True)
        response = auth(client, staff).get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_admin_role_without_is_staff_is_still_forbidden(self, client):
        # Access depends on is_staff, not on role="admin"
        fake_admin = CustomUserFactory(admin=False, role="admin", is_staff=False)
        response = auth(client, fake_admin).get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestChangePasswordView:
    url = reverse("users:api-v1:change-password")

    def test_wrong_old_password_fails(self, client):
        user = CustomUserFactory()
        response = auth(client, user).post(
            self.url,
            {
                "old_password": "wrong",
                "new_password": "NewStrong123",
                "new_password1": "NewStrong123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success_changes_password(self, client):
        user = CustomUserFactory()  # factory default password: pass12345
        response = auth(client, user).post(
            self.url,
            {
                "old_password": "pass12345",
                "new_password": "NewStrong123",
                "new_password1": "NewStrong123",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        # Reload from the DB to see the saved password hash
        user.refresh_from_db()
        assert user.check_password("NewStrong123")


@pytest.mark.django_db
class TestTokenObtainView:
    url = reverse("users:api-v1:token_obtain_pair")

    def test_active_user_logs_in(self, client):
        user = CustomUserFactory(is_active=True)
        response = client.post(
            self.url,
            {
                "email": user.email,
                "password": "pass12345",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_inactive_user_blocked(self, client):
        user = CustomUserFactory(is_active=False)
        response = client.post(
            self.url,
            {
                "email": user.email,
                "password": "pass12345",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogoutView:
    url = reverse("users:api-v1:logout")

    def test_missing_refresh_field_fails(self, client):
        user = CustomUserFactory()
        response = auth(client, user).post(self.url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success_blacklists_token(self, client):
        user = CustomUserFactory()
        refresh = RefreshToken.for_user(user)

        response = auth(client, user).post(
            self.url, {"refresh": str(refresh)}, format="json"
        )
        assert response.status_code == status.HTTP_205_RESET_CONTENT

        # The blacklisted refresh token must no longer work
        refresh_url = reverse("users:api-v1:token_refresh")
        retry = client.post(refresh_url, {"refresh": str(refresh)}, format="json")
        assert retry.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestVerifyEmailView:
    url = reverse("users:api-v1:verify-email")

    def test_missing_token_fails(self, client):
        response = client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_token_fails(self, client):
        response = client.get(self.url, {"token": "does-not-exist"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_token_activates_user(self, client):
        user = CustomUserFactory(is_active=False)
        # Simulate what generate_verification_token stores in the cache
        cache.set("email_verify:good-token", user.id, timeout=900)

        response = client.get(self.url, {"token": "good-token"})

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True
        # The token is single-use, so it must be gone from the cache
        assert cache.get("email_verify:good-token") is None


@pytest.mark.django_db
class TestResendVerificationEmailView:
    url = reverse("users:api-v1:resend-verification-email")

    def test_nonexistent_email_returns_generic_success(self, client):
        # Same 200 response as a real email, to avoid leaking which emails exist
        response = client.post(self.url, {"email": "nobody@example.com"}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_already_active_user_fails(self, client):
        user = CustomUserFactory(is_active=True)
        response = client.post(self.url, {"email": user.email}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Here the names are patched in views.py, where this view imports them
    @patch("users.api.v1.views.send_verification_email_task")
    @patch("users.api.v1.views.generate_verification_token")
    def test_inactive_user_triggers_email(self, mock_token, mock_email, client):
        mock_token.return_value = "tok"
        user = CustomUserFactory(is_active=False)
        response = client.post(self.url, {"email": user.email}, format="json")
        assert response.status_code == status.HTTP_200_OK
        mock_email.delay.assert_called_once()
