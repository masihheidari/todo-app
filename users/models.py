from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom manager: users log in with email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Users must have an email address"))
        email = self.normalize_email(email)
        # New users stay inactive until they verify their email
        extra_fields.setdefault("is_active", False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Superusers are active and have full permissions from the start
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        # Guard against explicitly passing False for these flags
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Project user model (see AUTH_USER_MODEL in settings)."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    email = models.EmailField(unique=True, null=False, blank=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    # Accounts stay inactive until the email is verified
    is_active = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Log in with email; these fields are asked for by createsuperuser
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.email
