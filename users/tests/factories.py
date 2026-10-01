import factory
from factory.django import DjangoModelFactory
from users.models import CustomUser
 
 
class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser
         
    
    username = factory.sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = CustomUser.Role.STUDENT
    is_active = True
    
    password = factory.PostGenerationMethodCall('set_password', 'pass12345')


    class Params:
        teacher = factory.Trait(role=CustomUser.Role.TEACHER)
        admin = factory.Trait(
            role=CustomUser.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )