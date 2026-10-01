from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import CustomUser

from ...tasks import send_verification_email_task
from ..utils import generate_verification_token


class CustomUserSerializer(ModelSerializer):
    """Public profile data a user can see about themselves."""

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "created_date",
            "updated_date",
        ]


class AdminUserSerializer(ModelSerializer):
    """Full user data for admins (used by the users list endpoint)."""

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "username",
            "is_active",
            "is_staff",
            "is_superuser",
            "first_name",
            "last_name",
            "created_date",
            "updated_date",
            "role",
        ]
        # These cannot be changed through the API
        read_only_fields = ["id", "created_date", "updated_date", "role"]


class RegistrationSerializer(ModelSerializer):
    """Validates sign-up data and creates an inactive user."""

    # write_only: accepted on input, never returned in responses
    password = serializers.CharField(max_length=255, min_length=8, write_only=True)
    # Confirmation field; must match `password`
    password1 = serializers.CharField(max_length=255, min_length=8, write_only=True)

    class Meta:
        model = CustomUser
        fields = ["email", "username", "password", "password1"]

    def validate(self, attrs):
        # Object-level validation: both passwords must be identical
        if attrs.get("password") != attrs.get("password1"):
            raise serializers.ValidationError({"detail": "passwords doesn't match"})

        # Run Django's AUTH_PASSWORD_VALIDATORS (length, common, numeric, ...)
        try:
            validate_password(attrs.get("password"))
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return super().validate(attrs)

    def create(self, validated_data):
        # password1 is only for confirmation; create_user doesn't accept it
        validated_data.pop("password1", None)
        user = CustomUser.objects.create_user(**validated_data)

        # Create a verification token and send the email in the background
        token = generate_verification_token(user.id)
        send_verification_email_task.delay(user.email, token)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login serializer that gives a clear error for unverified accounts."""

    def validate(self, attrs):
        email = attrs.get(self.username_field)
        password = attrs.get("password")

        user = CustomUser.objects.filter(email=email).first()

        # Only reveal "please verify" when the password is correct, so we don't
        # leak whether an unverified account exists to someone guessing passwords
        if user is not None and user.check_password(password) and not user.is_active:
            raise AuthenticationFailed(
                {"detail": "please verify your email before logging in"}
            )

        # Otherwise fall back to the default JWT login logic
        return super().validate(attrs)


class ChangePasswordSerializer(serializers.Serializer):
    """Input for changing the password. The old password is checked in the view."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True)  # confirmation

    # def validate_old_password(self, value):
    #     user = self.context['request'].user
    #     if not user.check_password(value):  # <-- this is where it is used
    #         raise serializers.ValidationError("old password is wrong")
    #     return value

    def validate(self, attrs):
        # New password and its confirmation must match
        if attrs.get("new_password") != attrs.get("new_password1"):
            raise serializers.ValidationError({"detail": "passwords doesn't match"})
        # Enforce the project's password strength rules
        try:
            validate_password(attrs.get("new_password"))
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return super().validate(attrs)


class ResendVerificationEmailSerializer(serializers.Serializer):
    """Only needs an email address (format is validated by EmailField)."""

    email = serializers.EmailField()
