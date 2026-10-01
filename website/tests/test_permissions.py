import pytest
from rest_framework.test import APIRequestFactory

from users.tests.factories import CustomUserFactory
from website.api.v1.permissions import IsAdminOrTeacher, IsOwner, IsWithin24HoursAndNotDone
from website.tests.factories import TaskFactory

factory = APIRequestFactory()


@pytest.mark.django_db
class TestIsOwner:
    def test_owner_can_access_own_task(self):
        user = CustomUserFactory()
        task = TaskFactory(author=user)
        request = factory.get('/')
        request.user = user
        assert IsOwner().has_object_permission(request, None, task) is True

    def test_non_owner_denied(self):
        user = CustomUserFactory()
        other = CustomUserFactory()
        task = TaskFactory(author=other)
        request = factory.get('/')
        request.user = user
        assert IsOwner().has_object_permission(request, None, task) is False

    def test_teacher_bypasses_ownership(self):
        teacher = CustomUserFactory(teacher=True)
        task = TaskFactory()  # مال یک نویسنده‌ی دیگر
        request = factory.get('/')
        request.user = teacher
        assert IsOwner().has_object_permission(request, None, task) is True


@pytest.mark.django_db
class TestIsAdminOrTeacher:
    def test_student_denied(self):
        student = CustomUserFactory()
        request = factory.get('/')
        request.user = student
        assert IsAdminOrTeacher().has_permission(request, None) is False

    def test_teacher_allowed(self):
        teacher = CustomUserFactory(teacher=True)
        request = factory.get('/')
        request.user = teacher
        assert IsAdminOrTeacher().has_permission(request, None) is True


@pytest.mark.django_db
class TestIsWithin24HoursAndNotDone:
    def test_recent_and_not_done_allowed(self):
        task = TaskFactory(is_done=False)
        request = factory.patch('/')
        request.user = task.author
        assert IsWithin24HoursAndNotDone().has_object_permission(request, None, task) is True

    def test_done_task_denied(self):
        task = TaskFactory(is_done=True)
        request = factory.patch('/')
        request.user = task.author
        assert IsWithin24HoursAndNotDone().has_object_permission(request, None, task) is False