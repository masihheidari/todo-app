import pytest
from rest_framework.test import APIClient
from django.core.cache import cache


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="student@testuser.com", password="testpass1234@", is_active=True
    )


@pytest.fixture
def teacher_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="teacher@testuser.com",
        password="testpass1234@",
        is_active=True,
        role="teacher",
    )


@pytest.fixture
def admin_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="admin@testuser.com",
        password="testpass1234@",
        is_active=True,
        role="admin",
    )


@pytest.fixture
def auth_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture(autouse=True)
def use_local_memory_cache(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    # Start every test with an empty cache so tests don't affect each other
    cache.clear()
    yield
    cache.clear()
