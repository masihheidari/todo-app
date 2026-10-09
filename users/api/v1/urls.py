from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    CreateCustomUserView,
    CustomTokenObtainPairView,
    LogoutView,
    ResendVerificationEmailView,
    RetrieveUserView,
    UsersListView,
    VerifyEmailView,
)

...  # stray Ellipsis, harmless but can be removed

# Namespace used in reverse(), e.g. "users:api-v1:registration"
app_name = "api-v1"

urlpatterns = [
    # --- Account management ---
    path("registration/", CreateCustomUserView.as_view(), name="registration"),
    path("profile/", RetrieveUserView.as_view(), name="profile"),
    path("users/", UsersListView.as_view(), name="users-list"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # --- JWT authentication ---
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # --- Email verification ---
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification-email/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification-email",
    ),
]
