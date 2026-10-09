from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import CustomUser

from ...tasks import send_verification_email_task
from ..utils import generate_verification_token
from .serializer import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    CustomUserSerializer,
    RegistrationSerializer,
    ResendVerificationEmailSerializer,
)


class CreateCustomUserView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class RetrieveUserView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UsersListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "old password is wrong"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"detail": "password changed successfully"}, status=200)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response(
                {"detail": "this field is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        except TokenError:
            return Response(
                {"detail": "invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get("token")

        if not token:
            return Response(
                {"detail": "token not sent "}, status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = f"email_verify:{token}"
        user_id = cache.get(cache_key)

        if user_id is None:
            return Response(
                {"detail": " the link is invalid or expired "},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": " user not found "}, status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.save()

        cache.delete(cache_key)

        return Response(
            {"detail": " account successfully activated "}, status=status.HTTP_200_OK
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend_verification"

    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = CustomUser.objects.filter(email=email).first()

        generic_response = Response(
            {
                "detail": (
                    "if an account with this email exists, "
                    "a verification link has been sent"
                )
            },
            status=status.HTTP_200_OK,
        )

        if user is None:
            return generic_response

        if user.is_active:
            return Response(
                {"detail": "this account is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = generate_verification_token(user.id)
        send_verification_email_task.delay(user.email, token)
        return generic_response
