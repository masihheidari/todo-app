import pytest
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from website.api.v1.serializer import TeacherTaskSerializer

factory = APIRequestFactory()


def make_request(data):
    """Build a real DRF Request so that request.data works."""
    return Request(
        factory.patch("/", data, format="json"),
        parsers=[JSONParser()],
    )


@pytest.mark.django_db
class TestTeacherTaskSerializer:
    def test_cannot_change_is_done(self):
        request = make_request({"is_done": True})
        serializer = TeacherTaskSerializer(
            data={"title": "x", "content": "y", "is_done": True},
            context={"request": request},
        )
        assert not serializer.is_valid()
        assert "is_done" in serializer.errors

    def test_can_update_without_touching_is_done(self):
        request = make_request({"title": "new title"})
        serializer = TeacherTaskSerializer(
            data={"title": "new title", "content": "y"},
            context={"request": request},
        )
        assert serializer.is_valid(), serializer.errors
