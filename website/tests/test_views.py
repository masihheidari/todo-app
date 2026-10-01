import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.tests.factories import CustomUserFactory
from website.tests.factories import TaskFactory


@pytest.fixture
def client():
    return APIClient()


def auth(client, user):
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestTaskListQueryset:
    url = reverse('website:api-v1:task-list')

    def test_student_sees_only_own_tasks(self, client):
        student = CustomUserFactory()
        other = CustomUserFactory()
        TaskFactory(author=student, title='mine')
        TaskFactory(author=other, title='not-mine')

        response = auth(client, student).get(self.url)

        titles = [t['title'] for t in response.data]
        assert 'mine' in titles
        assert 'not-mine' not in titles

    def test_teacher_sees_all_tasks(self, client):
        teacher = CustomUserFactory(teacher=True)
        TaskFactory()
        TaskFactory()

        response = auth(client, teacher).get(self.url)

        assert len(response.data) == 2


@pytest.mark.django_db
class TestTaskCreateDeletePermissions:
    url = reverse('website:api-v1:task-list')

    def test_student_cannot_create(self, client):
        student = CustomUserFactory()
        response = auth(client, student).post(
            self.url, {'title': 'x', 'content': 'y'}, format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_teacher_can_create(self, client):
        teacher = CustomUserFactory(teacher=True)
        response = auth(client, teacher).post(
            self.url, {'title': 'x', 'content': 'y'}, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_student_cannot_delete(self, client):
        student = CustomUserFactory()
        task = TaskFactory(author=student)
        detail_url = reverse('website:api-v1:task-detail', args=[task.pk])

        response = auth(client, student).delete(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTaskListCaching:
    url = reverse('website:api-v1:task-list')

    def test_second_request_served_from_cache(self, client, django_assert_num_queries):
        student = CustomUserFactory()
        TaskFactory(author=student)
        c = auth(client, student)

        c.get(self.url)   
        with django_assert_num_queries(0):
            c.get(self.url)  

    def test_cache_invalidated_after_creating_task(self, client):
        teacher = CustomUserFactory(teacher=True)
        c = auth(client, teacher)

        c.get(self.url)      
        TaskFactory()    
        response = c.get(self.url)

        assert len(response.data) == 1