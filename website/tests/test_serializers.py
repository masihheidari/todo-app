import pytest
from rest_framework.test import APIRequestFactory

from website.api.v1.serializer import TeacherTaskSerializer

factory = APIRequestFactory()


@pytest.mark.django_db
class TestTeacherTaskSerializer:
    def test_cannot_change_is_done(self):
        request = factory.patch('/', {'is_done': True})
        serializer = TeacherTaskSerializer(
            data={'title': 'x', 'content': 'y', 'is_done': True},
            context={'request': request},
        )
        assert not serializer.is_valid()
        assert 'is_done' in serializer.errors

    def test_can_update_without_touching_is_done(self):
        request = factory.patch('/', {'title': 'new title'})
        serializer = TeacherTaskSerializer(
            data={'title': 'new title', 'content': 'y'},
            context={'request': request},
        )
        assert serializer.is_valid(), serializer.errors