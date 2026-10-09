import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from users.models import CustomUser
from users.tests.factories import CustomUserFactory


@pytest.mark.django_db
class TestCreateUser:
    def _make(self, **overrides):
        """Create a user with sensible defaults; override any field per test."""
        data = dict(
            email="ali@example.com",
            password="pass12345@",
            username="ali",
            first_name="Ali",
            last_name="Rezaei",
        )
        data.update(overrides)
        return CustomUser.objects.create_user(**data)

    def test_create_user_with_given_fields(self):
        user = self._make()
        assert user.email == "ali@example.com"
        assert user.username == "ali"
        assert user.pk is not None  # saved to the database

    def test_password_is_hashed(self):
        user = self._make(password="pass12345@")

        assert user.password != "pass12345@"
        assert user.check_password("pass12345@") is True

    def test_missing_email_raises_value_error(self):
        with pytest.raises(ValueError):
            CustomUser.objects.create_user(
                email="",
                password="pass12345@",
                username="x",
                first_name="v",
                last_name="y",
            )

    def test_email_is_normalized(self):
        # Only the domain part is lowercased
        user = self._make(email="Ali@EXAMPLE.COM")
        assert user.email == "Ali@example.com"

    def test_defaults_to_inactive(self):
        user = self._make()
        assert user.is_active is False

    def test_is_active_true_when_explicitly_passed(self):
        user = self._make(is_active=True)
        assert user.is_active is True

    def test_defaults_role_to_student(self):
        user = self._make()
        assert user.role == CustomUser.Role.STUDENT

    def test_is_staff_and_is_superuser_default_false(self):
        user = self._make()
        assert user.is_staff is False
        assert user.is_superuser is False


@pytest.mark.django_db
class TestCreateSuperuser:
    def _make(self, **overrides):
        data = dict(
            email="admin@example.com",
            password="pass12345",
            username="admin",
            first_name="Admin",
            last_name="User",
        )
        data.update(overrides)
        return CustomUser.objects.create_superuser(**data)

    def test_sets_staff_superuser_active(self):
        user = self._make()
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True

    def test_explicit_is_staff_false_raises(self):
        with pytest.raises(ValueError):
            self._make(is_staff=False)

    def test_explicit_is_superuser_false_raises(self):
        with pytest.raises(ValueError):
            self._make(is_superuser=False)


@pytest.mark.django_db
class TestCustomUserModel:
    def test_str_returns_email(self):
        user = CustomUserFactory(email="sara@example.com")
        assert str(user) == "sara@example.com"

    def test_duplicate_email_raises_integrity_error(self):
        CustomUserFactory(email="dup@example.com")
        # atomic() keeps the test's transaction usable after the DB error
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                CustomUserFactory(email="dup@example.com")

    def test_duplicate_username_raises_integrity_error(self):
        CustomUserFactory(username="same")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                CustomUserFactory(username="same")

    def test_same_role_not_unique(self):
        # Many users may share the same role
        CustomUserFactory(teacher=True)
        CustomUserFactory(teacher=True)
        assert CustomUser.objects.filter(role=CustomUser.Role.TEACHER).count() == 2


@pytest.mark.django_db
class TestCustomUserValidation:
    # full_clean() runs field validators, which .save() does not

    def test_blank_email_fails_full_clean(self):
        user = CustomUser(
            username="x",
            first_name="X",
            last_name="Y",
            email="",
        )
        with pytest.raises(ValidationError) as exc_info:
            user.full_clean()
        assert "email" in exc_info.value.message_dict

    def test_invalid_role_fails_full_clean(self):
        user = CustomUser(
            username="x",
            first_name="X",
            last_name="Y",
            email="x@example.com",
            role="not-a-real-role",
        )
        with pytest.raises(ValidationError) as exc_info:
            user.full_clean()
        assert "role" in exc_info.value.message_dict

    def test_valid_user_passes_full_clean(self):
        user = CustomUser(
            username="x",
            first_name="X",
            last_name="Y",
            email="x@example.com",
        )
        # password is not set in this test, so skip it in the validation
        user.full_clean(exclude=["password"])
