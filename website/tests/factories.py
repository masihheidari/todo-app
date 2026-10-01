import factory
from factory.django import DjangoModelFactory

from users.tests.factories import CustomUserFactory
from website.models import Task


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f'Task {n}')
    content = 'some content'
    author = factory.SubFactory(CustomUserFactory)