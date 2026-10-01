import pytest
from django.core.cache import cache

from users.models import CustomUser
from website.tests.factories import TaskFactory


@pytest.mark.django_db
def test_creating_task_clears_author_and_role_caches():
    task = TaskFactory()
    cache.set(f'task_list_user_{task.author_id}', 'stale')
    cache.set(f'task_list_role_{CustomUser.Role.ADMIN}', 'stale')

    task.save()

    assert cache.get(f'task_list_user_{task.author_id}') is None
    assert cache.get(f'task_list_role_{CustomUser.Role.ADMIN}') is None


@pytest.mark.django_db
def test_deleting_task_clears_cache():
    task = TaskFactory()
    cache.set(f'task_list_user_{task.author_id}', 'stale')

    task.delete()

    assert cache.get(f'task_list_user_{task.author_id}') is None