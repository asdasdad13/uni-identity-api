from django.test import TestCase, tag
from django.utils.dateparse import parse_date

from .models import *
from .factory import *
import datetime


# Model tests

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
            identity = i1
        )

        # Profile that has no preferred name
        self.p2 = ProfileFactory.create(
            preferred_name = "",
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
    def test_no_preferred_name(self):
        profile = Profile.objects.get(pk=self.p2.pk)
        self.assertFalse(profile.preferred_name)
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

class AffiliationTestCase(TestCase):
    def setUp(self):
        self.i1 = CompleteIdentityFactory.create()
        self.i2 = CompleteIdentityFactory.create(create_roles=2)
        
    @tag("database")
    def test_roles_exist(self):
        i1_roles = IdentityAffiliation.objects.filter(identity=self.i1).count()
        i2_roles = IdentityAffiliation.objects.filter(identity=self.i2).count()

        # Number of roles
        self.assertEqual(i1_roles, 1)
        self.assertEqual(i2_roles, 2)
    
    @tag("database")
    def test_add_roles(self):
        club = AffiliationFactory.create(
            uid='Chess_Club',
            name='University Chess Club',
            affiliation_type='CLUB'
        )

        IdentityAffiliation.objects.create(
            identity=self.i1,
            affiliation=club,
            role_name='CM',
        )

        i1_roles = IdentityAffiliation.objects.filter(identity=self.i1).count()
        self.assertEqual(i1_roles, 2)

    @tag("database")
    def test_delete_roles(self):
        # Setup: Get the existing affiliation link
        aff_link = self.i1.affiliations.first()
        self.assertIsNotNone(aff_link, "Identity should have at least one role from factory.")

        target_uid = aff_link.affiliation.uid

        aff_link.delete()

        i1_roles_after = self.i1.affiliations.count()
        self.assertEqual(i1_roles_after, 0)

        self.assertTrue(
        Affiliation.objects.filter(uid=target_uid).exists(),
        "The Course/Club entity should persist even after the user relationship is deleted."
    )
        
    @tag("database")
    def test_is_active(self):
        # Get a junction record
        r1 = IdentityAffiliation.objects.filter(identity=self.i1).first()
        self.assertTrue(r1.is_active)

        # Set to inactive (Pending/Revoked)
        r1.is_active = False
        r1.save()

        self.assertFalse(IdentityAffiliation.objects.get(id=r1.id).is_active)
        # Check counts across the whole database
        self.assertEqual(IdentityAffiliation.objects.filter(is_active=False).count(), 1)
        self.assertEqual(IdentityAffiliation.objects.filter(is_active=True).count(), 2)