from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
import hashlib
import base64
import secrets
from urllib.parse import urlencode
from django.conf import settings
from api.utils import get_token
from core.utils import oauth_required

APP_NAME = 'clubs'

HOST_BASE_URL = settings.HOST_BASE_URL
CLIENT_ID = settings.CLUB_DIRECTORY_CLIENT_ID
CLIENT_SECRET = settings.CLUB_DIRECTORY_CLIENT_SECRET
REDIRECT_URI = f"{HOST_BASE_URL}/{APP_NAME}/callback/"


@oauth_required(app_name=APP_NAME)
def index(request):
    """Club Directory homepage, requires OAuth authorisation (redirects to login if not yet authorised)."""

    # Get user data through calling internal API GET request.
    token = get_token(request)
    url = f"{HOST_BASE_URL}/api/me/"
    headers = {'Authorization': f"Bearer {token}", 'context': 'clubs'}

    # Call internal REST API to get data
    api_response = requests.get(url=url, headers=headers)
    
    if api_response.status_code == 200:
        data = api_response.json()
        affiliations = data.get('affiliations', [])

        context = {
            'name': data.get('display_name'),
            'clubs': [a for a in affiliations if a['affiliation_type'] == 'CLUB'],
            }
        return render(request, 'clubs/index.html', context)

    return HttpResponse("Failed to fetch identity data", status=api_response.status_code)


def login(request):
    """Login view initiating OAuth flow"""
    # Generate PKCE
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
    
    # Store verifier for later
    request.session['pkce_verifier'] = code_verifier
    request.session['oauth_state'] = secrets.token_urlsafe(16)
    
    # Build authorisation URL
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid profile identity affiliations:courses',
        'state': request.session['oauth_state'],
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"{HOST_BASE_URL}/o/authorize/?{urlencode(params)}"
    return redirect(auth_url)


def revoke(request):
    """Revoke app access"""
    session_key = f'{APP_NAME}_access_token'
    access_token = request.session[session_key]

    params = {
        'token': access_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    if access_token:
        requests.post(f"{HOST_BASE_URL}/o/revoke_token/", data=params)
        del request.session[session_key]
        
    return redirect('core:index')


def callback(request):
    """Handle OAuth callback."""
    # Verify state (CSRF protection)
    if request.GET.get('state') != request.session.get('oauth_state'):
        return HttpResponse("Invalid state parameter", status=400)
    
    # Get authorization code
    code = request.GET.get('code')
    if not code:
        return HttpResponse("No authorization code received", status=400)

    code_verifier = request.session.get('pkce_verifier')

    # Exchange code for tokens from client to server.
    token_response = requests.post(
        f'{HOST_BASE_URL}/o/token/',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code_verifier': code_verifier
        }
    )

    if token_response.status_code != 200:
        return HttpResponse(f"Token exchange failed: {token_response.text}", status=400)
    
    tokens = token_response.json()
    
    # Get user info
    userinfo_response = requests.get(
        f"{HOST_BASE_URL}/o/userinfo/",
        headers={'Authorization': f"Bearer {tokens['access_token']}"}
    )

    userinfo = userinfo_response.json()

    # Store user in session
    request.session['user'] = {
        'sub': userinfo['sub'],
        'name': userinfo['name'],
    }

    request.session['clubs'] = userinfo.get('affiliations:clubs', [])
    request.session['access_token'] = tokens['access_token']
    # Track specific tokens for revoking authorisation option
    request.session[f'{APP_NAME}_access_token'] = tokens['access_token']

    # Clean up OAuth session data
    del request.session['pkce_verifier']
    del request.session['oauth_state']

    next_url = request.session.pop('oauth_next', 'clubs:index')
    return redirect(next_url)


@oauth_required(app_name=APP_NAME)
def view_roster(request, roster_type, affiliation_id):
    """Universal HTMX fragment for any roster type (course, module, etc)."""
    token = get_token(request)

    # Dynamically build the API URL based on the type
    # Matches the API structure: /api/roster/course/CS101/
    url = f"{HOST_BASE_URL}/api/roster/{roster_type}/{affiliation_id}/"
    headers = {'Authorization': f"Bearer {token}", 'context': 'clubs'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        aff = response.json()

    except Exception:
        aff = []

    context = {
        'aff': aff,
    }
    
    return render(request, 'clubs/partials/roster_list.html', context)