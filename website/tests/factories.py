import factory
from factory.django import DjangoModelFactory

from users.tests.factories import CustomUserFactory
from website.models import Task


class TaskFactory(DjangoModelFactory):
    """Builds tasks for tests; each task gets its own new author by default."""

    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    content = "some content"
    # Creates a fresh user per task; pass author=... to reuse an existing one
    author = factory.SubFactory(CustomUserFactory)
