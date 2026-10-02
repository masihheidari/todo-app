import pytest
from rest_framework.test import APIRequestFactory

from users.tests.factories import CustomUserFactory
from website.api.v1.permissions import IsAdminOrTeacher, IsOwner
from website.tests.factories import TaskFactory

# Builds fake requests without going through URL routing or middleware
factory = APIRequestFactory()


@pytest.mark.django_db
class TestIsOwner:
    def test_owner_can_access_own_task(self):
        user = CustomUserFactory()
        task = TaskFactory(author=user)
        request = factory.get("/")
        request.user = user
        assert IsOwner().has_object_permission(request, None, task) is True

    def test_non_owner_denied(self):
        user = CustomUserFactory()
        other = CustomUserFactory()
        task = TaskFactory(author=other)
        request = factory.get("/")
        request.user = user
        assert IsOwner().has_object_permission(request, None, task) is False

    def test_teacher_bypasses_ownership(self):
        teacher = CustomUserFactory(teacher=True)
        task = TaskFactory()  # belongs to a different author
        request = factory.get("/")
        request.user = teacher
        assert IsOwner().has_object_permission(request, None, task) is True


@pytest.mark.django_db
class TestIsAdminOrTeacher:
    def test_student_denied(self):
        student = CustomUserFactory()
        request = factory.get("/")
        request.user = student
        assert IsAdminOrTeacher().has_permission(request, None) is False

    def test_teacher_allowed(self):
        teacher = CustomUserFactory(teacher=True)
        request = factory.get("/")
        request.user = teacher
        assert IsAdminOrTeacher().has_permission(request, None) is True
