from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from website.cache_utils import task_list_cache_key
from website.models import Task

from .permissions import IsAdminOrTeacher, IsOwner
from .serializer import (
    AdminTaskSerializer,
    StudentTaskSerializer,
    TeacherTaskSerializer,
)


class TaskModelViewSet(viewsets.ModelViewSet):
    """CRUD for tasks, with role-based access and a cached list endpoint."""

    def list(self, request, *args, **kwargs):
        # Serve the list from Redis when possible
        cache_key = task_list_cache_key(request.user)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Cache miss: build the response normally, then cache it for 5 minutes.
        # The cache is cleared by website.signals when a task changes.
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response

    def get_permissions(self):
        # Only admins/teachers can create or delete tasks
        if self.action in ["create", "destroy"]:
            permission_classes = [IsAuthenticated, IsAdminOrTeacher]
        else:
            # Everything else: students need to be the owner of the task
            permission_classes = [IsAuthenticated, IsOwner]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        user = self.request.user
        # e.g. swagger schema generation runs without a logged-in user
        if not user.is_authenticated:
            return AdminTaskSerializer

        # On updates, each role gets different editable fields
        if self.action in ["update", "partial_update"]:
            if user.role == user.Role.STUDENT:
                return StudentTaskSerializer
            if user.role == user.Role.TEACHER:
                return TeacherTaskSerializer
            return AdminTaskSerializer  # Admin

        # list / retrieve / create
        return AdminTaskSerializer

    def get_queryset(self):
        user = self.request.user
        # Admins and teachers see everything, students only their own tasks
        if user.role in [user.Role.ADMIN, user.Role.TEACHER]:
            return Task.objects.all()
        return Task.objects.filter(author=user)

    def perform_create(self, serializer):
        # The author is always the logged-in user, never taken from the request
        serializer.save(author=self.request.user)
