from core.factory import *

from django.test import tag
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken


class IdentityApiTests(APITestCase):
    def setUp(self):
        self.identity = IdentityFactory.create()
        self.url = reverse('api:identity_me')

    @tag('API')
    def test_get_identity_with_valid_token(self):
        token = AccessToken.for_user(self.identity.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        year_prefix = str(datetime.datetime.now().year)
        self.assertEqual(response.data['institutional_id'], f'STU{year_prefix}000001W')

    @tag('API')
    def test_get_identity_unauthorized(self):
        # No credentials provided
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)