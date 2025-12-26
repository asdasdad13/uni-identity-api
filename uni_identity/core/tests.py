from django.test import TestCase, tag
from django.utils.dateparse import parse_date

from .models import *
from .factory import *


# Models

class IdentityTestCase(TestCase):
    def setUp(self):
        self.i1 = IdentityFactory.create(
            legal_forenames = 'John',
            legal_surname = 'Doe',
            effective_date = parse_date('2025-01-01')
        )

    @tag("database")
    def test_identity_pk(self):
        self.assertIsNotNone(self.i1)
        self.assertIsNotNone(self.i1.pk)
    
    @tag("database")
    def test_identity_exists_in_database(self):
        identity: QuerySet = Identity.objects.get(pk=self.i1.pk)
        self.assertTrue(identity)

    @tag("fields")
    def test_identity_has_correct_fields(self):
        identity: QuerySet = Identity.objects.get(pk=self.i1.pk)
        self.assertEqual(self.i1.legal_forenames, identity.legal_forenames)
        self.assertEqual(self.i1.legal_surname, identity.legal_surname)

        expected_full_name: str = " ".join([self.i1.legal_forenames, self.i1.legal_surname])
        self.assertEqual(expected_full_name, identity.full_name)

    def test_identity_institutional_id_generation(self):
        self.assertEqual(self.i1.institutional_id, 'STU2025000001W')


