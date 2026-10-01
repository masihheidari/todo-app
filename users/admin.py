from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_superuser", "is_active", "role")
    list_filter = ("email", "is_superuser", "is_active", "role")

    search_fields = ("email",)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "username",
                    "role",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
    )
    fieldsets = (
        (
            "Authentication",
            {
                "fields": ("email", "password", "username", "role"),
            },
        ),
        (
            "Permission",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                )
            },
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
