from django.shortcuts import render, redirect
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
import requests
import hashlib
import base64
import secrets
from urllib.parse import urlencode
from django.conf import settings
from functools import wraps
from api.utils import get_token


IDP_BASE = settings.IDP_BASE_URL
CLIENT_ID = settings.LMS_CLIENT_ID
CLIENT_SECRET = settings.LMS_CLIENT_SECRET
REDIRECT_URI = f"{IDP_BASE}/lms/callback/"


def oauth_required(view_func):
    """
    Decorator to require OAuth authorisation.
    User must be logged into IdP AND have authorized decorated app via OAuth.
    Redirects unauthorised users to login view.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is logged into IdP
        if not request.user.is_authenticated:
            # Not logged in, redirect to IdP login
            return redirect_to_login(request.get_full_path())
        
        # User is logged in, check if they've authorised via OAuth
        if 'user' not in request.session:
            # Not authorised, start OAuth flow
            return redirect('lms:login')
        
        # Proceed to view
        return view_func(request, *args, **kwargs)
    
    return wrapper


@oauth_required
def index(request):
    """LMS homepage, requires OAuth authorisation (redirects to login if not yet authorised)."""

    # Get user data through calling internal API GET request.
    token = get_token(request)
    url = f"{IDP_BASE}/api/me/"
    headers = {'Authorization': f"Bearer {token}", 'context': 'lms'}

    # Call internal REST API to get data
    api_response = requests.get(url=url, headers=headers)
    
    #TODO: get list of courses and modules (separately) from API

    if api_response.status_code == 200:
        data = api_response.json()
        affiliations = data.get('affiliations', [])

        context = {
            'name': data.get('display_name'),
            'courses': [a for a in affiliations if a['affiliation_type'] == 'COURSE'],
            'modules': [a for a in affiliations if a['affiliation_type'] == 'MOD'],}
        return render(request, 'lms/index.html', context)

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
        'scope': 'openid profile affiliations:courses',
        'state': request.session['oauth_state'],
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"{IDP_BASE}/o/authorize/?{urlencode(params)}"
    return redirect(auth_url)


def logout(request):
    """Log user out and revoke user's access token."""
    request.session.flush()
    return redirect('lms:index')


def logout_and_revoke(request):
    """Logout and revoke app access"""
    print(request.session.keys())
    access_token = request.session['api_access_token']

    params = {
        'token': access_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    if access_token:
        # Revoke token
        requests.post(f"{IDP_BASE}/o/revoke_token/?{urlencode(params)}")
    
    return redirect('lms:index')


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
        f'{IDP_BASE}/o/token/',
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
        f"{IDP_BASE}/o/userinfo/",
        headers={'Authorization': f"Bearer {tokens['access_token']}"}
    )

    userinfo = userinfo_response.json()

    # Store user in session
    request.session['user'] = {
        'sub': userinfo['sub'],
        'name': userinfo['name'],
        'status': userinfo.get('status')
    }

    request.session['courses'] = userinfo.get('affiliations:courses', [])
    request.session['access_token'] = tokens['access_token']

    # Clean up OAuth session data
    del request.session['pkce_verifier']
    del request.session['oauth_state']

    next_url = request.session.pop('oauth_next', 'lms:index')
    return redirect(next_url)


@oauth_required
def view_roster(request, roster_type, affiliation_id):
    """Universal HTMX fragment for any roster type (course, module, etc)."""
    token = get_token(request)

    # Dynamically build the API URL based on the type
    # Matches the API structure: /api/roster/course/CS101/
    url = f"{IDP_BASE}/api/roster/{roster_type}/{affiliation_id}/"
    headers = {'Authorization': f"Bearer {token}", 'context': 'lms'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        classmates = response.json()

    except Exception:
        classmates = []

    context = {
        'classmates': classmates,
        'affiliation_id': affiliation_id,
    }
    
    return render(request, 'lms/partials/roster_list.html', context)