from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from core.factory import IdentityFactory, ProfileFactory, AffiliationFactory


class LmsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.i1 = IdentityFactory.create()
        self.u1 = self.i1.user
        self.p1 = ProfileFactory.create(identity=self.i1)
        self.r1 = self.i1.affiliations.first()

    def force_authenticate_session(self, courses=None):
        """Helper to bypass @oauth_required and prime the session."""
        self.client.force_login(self.u1)
        session = self.client.session

        # @oauth_required checks if user is session-authenticated.
        # Prime the session with required info to bypass interactive
        # PKCE flow.

        session['user'] = {
            'sub': self.i1.institutional_id,
        }

        if courses is not None:
            session['courses'] = courses

        session.save()

    @patch('requests.get')
    def test_lms_index_renders_with_api_data(self, mock_get):
        # Assert user exists in database
        self.assertEqual(self.i1.institutional_id, 'STU2026000001W')

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'display_name': 'Preferred Name',
            'institutional_id': '12345',
        }

        # Redirect unauthenticated users from /lms (index) to /login
        response = self.client.get(reverse('lms:index'))
        self.assertEqual(response.status_code, 302)

        # Simulate a logged-in OIDC session
        self.force_authenticate_session()
        response = self.client.get(reverse('lms:index'))
        self.assertEqual(response.status_code, 200)

        # /lms view contains information returned from API from database query
        self.assertContains(response, "Preferred Name")

    @patch('requests.get')
    def test_lms_index_context_data(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'display_name': 'Preferred Name',
            'institutional_id': '12345',
            'affiliations': [
                {'affiliation_type': 'COURSE', 'affiliation_id': 'CS101', 'role_name': 'Student'},
                {'affiliation_type': 'COURSE', 'affiliation_id': 'CS102', 'role_name': 'Rep'}
            ]
        }
        
        self.force_authenticate_session()

        response = self.client.get(reverse('lms:index'))

        # Check the context dictionary
        self.assertEqual(len(response.context['courses']), 2)
        self.assertEqual(response.context['courses'][0]['affiliation_id'], 'CS101')
        self.assertEqual(response.context['courses'][1]['role_name'], 'Rep')