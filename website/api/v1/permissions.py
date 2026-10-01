from datetime import timedelta

from django.utils import timezone
from rest_framework import permissions


class IsWithin24HoursAndNotDone(permissions.BasePermission):
    """Allow changes only during the first 24 hours and while not done."""

    def has_object_permission(self, request, view, obj):
        now = timezone.now()
        time_since_creation = now - obj.created_date
        day_hours = timedelta(hours=24)
        # Reading (GET, HEAD, OPTIONS) is always allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        # Too old to modify
        if time_since_creation > day_hours:
            return False
        # Finished tasks are locked
        if obj.is_done:
            return False
        return True


class IsOwner(permissions.BasePermission):
    """Object-level check: only the author may access a task."""

    def has_object_permission(self, request, view, obj):
        # Admins and teachers can access any task
        if request.user.role in [request.user.Role.ADMIN, request.user.Role.TEACHER]:
            return True
        return obj.author == request.user


class IsAdminOrTeacher(permissions.BasePermission):
    """View-level check: only admins and teachers (used for create/delete)."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            request.user.Role.ADMIN,
            request.user.Role.TEACHER,
        ]
