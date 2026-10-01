from django.urls import include, path

# Namespace for reverse(), e.g. reverse("users:api-v1:profile")
app_name = "users"

urlpatterns = [
    # All API endpoints live under /users/api/v1/
    path("api/v1/", include("users.api.v1.urls")),
]
