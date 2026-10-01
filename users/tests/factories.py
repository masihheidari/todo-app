import factory
from factory.django import DjangoModelFactory

from users.models import CustomUser


class CustomUserFactory(DjangoModelFactory):
    """Builds ready-to-use test users (active, password "pass12345")."""

    class Meta:
        model = CustomUser

    # user0, user1, ... so usernames are always unique
    username = factory.sequence(lambda n: f"user{n}")
    # Derived from the username, e.g. user0@example.com
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = CustomUser.Role.STUDENT
    # Active by default so tests can log in without email verification
    is_active = True

    # Hashes the password after the object is created
    password = factory.PostGenerationMethodCall("set_password", "pass12345")

    class Params:
        # Shortcuts: CustomUserFactory(teacher=True) / CustomUserFactory(admin=True)
        teacher = factory.Trait(role=CustomUser.Role.TEACHER)
        admin = factory.Trait(
            role=CustomUser.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
