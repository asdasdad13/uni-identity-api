"""factory_boy for testing models."""
import factory
import factory.random
from django.utils.dateparse import parse_date
from django.contrib.auth.models import User

from .models import *


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_staff = False

    @factory.lazy_attribute
    def username(self):     # john1
        random_int = factory.random.randgen.randint(100,999)
        return f"{self.first_name.lower()}{random_int}"


class AdminFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = "Ad"
    last_name = "Min"
    admin = True
    is_superuser = True


class IdentityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Identity

    user = factory.SubFactory(UserFactory)
    legal_forenames = factory.Faker("first_name")
    legal_surname = factory.Faker("last_name")
    effective_date = factory.Faker("date_object")
    date_of_birth = factory.Faker(
        "date_between_dates",
        date_start=factory.SelfAttribute("..effective_date"),
    )
    status = "STU"

class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(IdentityFactory)
    preferred_name = "Joanna"