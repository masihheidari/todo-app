from rest_framework import permissions


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
