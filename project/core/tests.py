from django.test import TestCase, tag
from django.utils.dateparse import parse_date

from .models import *
from .factory import *
import datetime


# Models

class IdentityTestCase(TestCase):
    def setUp(self):
        self.i1 = IdentityFactory.create(
            legal_forenames = 'John',
            legal_surname = 'Doe',
            effective_date = parse_date('2025-01-01')
        )
        self.i2 = IdentityFactory.create()

    @tag("database")
    def test_identity_pk(self):
        self.assertIsNotNone(self.i1)
        self.assertIsNotNone(self.i1.pk)
    
    @tag("database")
    def test_identity_exists_in_database(self):
        identity: QuerySet = Identity.objects.get(pk=self.i1.pk)
        self.assertTrue(identity)

    @tag("database")
    def test_identity_has_correct_fields(self):
        identity: QuerySet = Identity.objects.get(pk=self.i1.pk)
        self.assertEqual(self.i1.legal_forenames, identity.legal_forenames)
        self.assertEqual(self.i1.legal_surname, identity.legal_surname)

        expected_full_name: str = " ".join([self.i1.legal_forenames, self.i1.legal_surname])
        self.assertEqual(expected_full_name, identity.full_name)

    @tag("database")
    def test_identity_institutional_id_generation(self):
        year_prefix = str(datetime.datetime.now().year)

        self.assertEqual(self.i1.institutional_id, f'STU{year_prefix}000001W')
        self.assertNotEqual(self.i1.institutional_id, self.i2.institutional_id)


class ProfileTestCase(TestCase):
    def setUp(self):
        # Check identity and linked profile for the same person
        i1 = IdentityFactory.create(
            legal_forenames = 'John',
            legal_surname = 'Doe',
            effective_date = parse_date('2025-01-01'),
        )

        self.p1 = ProfileFactory.create(
            preferred_name = "Joanna",
            name_type = 'Preferred name',
            identity = i1
        )

        # Profile that has no preferred name
        self.p2 = ProfileFactory.create(
            preferred_name = "",
            name_type = ''
        )

    @tag("database")
    def test_profile_pk(self):
        self.assertIsNotNone(self.p1)
        self.assertIsNotNone(self.p1.pk)
    
    @tag("database")
    def test_profile_exists(self):
        profile = Profile.objects.get(pk=self.p1.pk)
        self.assertTrue(profile)

    @tag("database")
    def test_identity_exists(self):
        profile = Profile.objects.get(pk=self.p1.pk)
        linked_identity = profile.identity
        self.assertTrue(linked_identity)
    
    @tag("database")
    def test_abbreviated_name(self):    # Generated dynamically by Django ORM
        # John Doe -> J. Doe
        profile = Profile.objects.get(pk=self.p1.pk)
        self.assertEqual(profile.abbreviated_name, 'J. Doe')

    @tag("database")
    def test_identitys_preferred_name(self):
        # Get John's preferred name from Profile -> Identity
        profile = Profile.objects.get(
            identity__legal_forenames='John',
            identity__legal_surname='Doe'
            )
        self.assertEqual(profile.preferred_name, self.p1.preferred_name)

    @tag("database")
    def test_name_type(self):
        profile = Profile.objects.get(pk=self.p1.pk)
        self.assertEqual(profile.name_type, self.p1.name_type)

    @tag("database")
    def test_no_preferred_name(self):
        profile = Profile.objects.get(pk=self.p2.pk)
        self.assertFalse(profile.preferred_name)
        self.assertFalse(profile.name_type)
        self.assertTrue(profile.abbreviated_name)
        
    @tag("database")
    def test_delete_profile(self):
        pk1 = self.p1.pk
        self.assertTrue(Profile.objects.filter(pk=pk1).exists())

        Profile.objects.get(pk=pk1).delete()
        self.assertFalse(Profile.objects.filter(pk=pk1).exists())
        # Identity still exists
        self.assertTrue(Identity.objects.filter(pk=pk1).exists())

    @tag("database")
    def test_delete_identity(self):
        pk2 = self.p2.pk
        self.assertTrue(Identity.objects.filter(pk=pk2).exists())
        self.assertTrue(Profile.objects.filter(pk=pk2).exists())

        Identity.objects.get(pk=pk2).delete()

        # Identity deletion cascades with Profile
        self.assertFalse(Identity.objects.filter(pk=pk2).exists())
        self.assertFalse(Profile.objects.filter(pk=pk2).exists())

class RolesAndAffiliationsTestCase(TestCase):
    def setUp(self):
        self.i1 = CompleteIdentityFactory.create()
        self.i2 = CompleteIdentityFactory.create(create_roles=2)
        
    @tag("database")
    def test_roles_exist(self):
        i1_roles = RolesAndAffiliations.objects.filter(identity=self.i1).count()
        i2_roles = RolesAndAffiliations.objects.filter(identity=self.i2).count()

        # Number of roles
        self.assertEqual(i1_roles, 1)
        self.assertEqual(i2_roles, 2)
    
    @tag("database")
    def test_add_roles(self):
        RolesAndAffiliationsFactory.create(
            identity=self.i1,
            role_name='CM',
            affiliation_type='CLUB',
            affiliation_id='Chess_Club',
            is_active = True
        )

        i1_roles = RolesAndAffiliations.objects.filter(identity=self.i1).count()
        self.assertEqual(i1_roles, 2)

    @tag("database")
    def test_delete_roles(self):
        # Before deletion, i1 should have 1 role
        i1_roles = RolesAndAffiliations.objects.filter(identity=self.i1).count()
        self.assertEqual(i1_roles, 1)

        # Delete the 1 record of a role
        RolesAndAffiliations.objects.get(identity=self.i1).delete()
        i1_roles_2 = RolesAndAffiliations.objects.filter(identity=self.i1).count()
        self.assertEqual(i1_roles_2, 0)

    @tag("database")
    def test_is_active(self):
        r1 = RolesAndAffiliations.objects.get(identity=self.i1)
        self.assertTrue(r1.is_active)

        # Set a role to inactive
        r1.is_active = False
        r1.save()

        self.assertFalse(RolesAndAffiliations.objects.get(identity=self.i1).is_active)
        self.assertEqual(RolesAndAffiliations.objects.filter(is_active=False).count(), 1)
        self.assertEqual(RolesAndAffiliations.objects.filter(is_active=True).count(), 2)