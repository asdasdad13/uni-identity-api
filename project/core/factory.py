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

    # Automatically create profile on creation of Identity
    @factory.post_generation
    def create_profile(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if not extracted:
            return
        
        ProfileFactory(identity=obj)

    # Automatically create at least 1 role on creation of Identity 
    @factory.post_generation
    def create_roles(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # A number was passed in as argument while creating
            for _ in range(extracted):
                RolesAndAffiliationsFactory(identity=obj)

        else:   # Default behaviour: always create at least one role
            RolesAndAffiliationsFactory(identity=obj)


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    identity = factory.SubFactory(IdentityFactory)
    # Optional columns
    preferred_name = "Joanna"
    name_type = 'Preferred name'

    # Dynamically created abbreviated_name

class RolesAndAffiliationsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RolesAndAffiliations

    identity = factory.SubFactory(IdentityFactory)
    role_name = 'UG'
    affiliation_type = 'COURSE'
    affiliation_id = 'CS_UG_2024'
    is_active = True