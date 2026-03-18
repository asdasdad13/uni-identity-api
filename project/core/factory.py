"""factory_boy for testing models."""
import factory
from core.utils import generate_email
from .models import *
from django.contrib.auth.hashers import make_password


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        exclude = ('temp_first', 'temp_last', 'domain_val')

    temp_first = factory.Faker('first_name')
    temp_last = factory.Faker('last_name')

    first_name = ""
    last_name = ""
    is_staff = False
    domain_val = "@uni.ac.uk"
    password = factory.django.Password('pw')

    @factory.lazy_attribute
    def username(self):
        return generate_email(self.temp_first, self.temp_last, self.domain_val)
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if extracted is None:
            self.password = UserFactory.PASSWORD
        else:
            self.password = make_password(extracted)
UserFactory.PASSWORD = make_password('password')
    

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
                IdentityAffiliationFactory(identity=obj)

        else:   # Default behaviour: always create at least one role
            IdentityAffiliationFactory(identity=obj)


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    identity = factory.SubFactory(IdentityFactory)
    # Optional columns
    preferred_name = factory.Faker("name")

    # Dynamically created abbreviated_name


class AffiliationFactory(factory.django.DjangoModelFactory):
    """Creates the 'Source of Truth' entities (Courses, Clubs, etc.)"""

    class Meta:
        model = Affiliation
        django_get_or_create = ('uid',) # Prevent duplicate UID errors in tests

    uid = factory.Sequence(lambda n: f"COURSE_{n}")
    name = factory.Sequence(lambda n: f"Generic Course {n}")
    affiliation_type = 'COURSE'


class IdentityAffiliationFactory(factory.django.DjangoModelFactory):
    """Creates the link between a user and their affiliation."""

    class Meta:
        model = IdentityAffiliation

    identity = factory.SubFactory(IdentityFactory)
    affiliation = factory.SubFactory(AffiliationFactory)
    role_name = 'UG'
    is_active=True


class CompleteIdentityFactory(IdentityFactory):
    # Automatically create profile on creation of Identity
    @factory.post_generation
    def create_profile(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            ProfileFactory(identity=obj)

    # Automatically create at least 1 role on creation of Identity 
    @factory.post_generation
    def create_roles(obj, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            # A number was passed in as argument while creating
            for _ in range(extracted):
                IdentityAffiliationFactory(identity=obj)

        else:   # Default behaviour: always create at least one role
            IdentityAffiliationFactory(identity=obj)