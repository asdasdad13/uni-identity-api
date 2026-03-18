import hashlib
import base64
import secrets
import requests
from urllib.parse import urlencode
import json

BASE_URL = "http://127.0.0.1:8000"

APPLICATIONS = {
    'LMS': {    # Preferred name
        'client_id': 'qjhxpWe3OmV4KCBAXvX2VQJLGaMkQNNqpikFz4pw',
        'client_secret': '7Umz9mUPuuozzg73vM34d0KYPye78tEOuUltnjP8H5hkva2JpRtZYXAOkYNfu6jS2OQB5TJUy0oHIq9p2TCryQYrzzilOp3t7YTJcMTZ0c4U3Np8spnaaIFOojOH5M2g',
        'redirect_uri': 'http://127.0.0.1:8000/test-callback/',
        'scopes': 'openid profile identity affiliations:courses',
    },
    'Club Directory': { # Preferred name
        'client_id': '0U1eKM5l0HpCGslKQChkw7kRQyl0iALOwUwABiGs',
        'client_secret': 'E1RontOUPioWb7I7SEAikll4hTgynNST4JGhFHryLMVuqV6NCrMCcIb0NX5FAkXNyistvdmIQ5rUJ6YuIutjwrMkY3wbb9b9sVQwtV7lIP2ffnBxuVoB4hoaoBYjK4bb',
        'redirect_uri': 'http://127.0.0.1:8000/test-callback/',
        'scopes': 'openid profile identity affiliations:clubs',
    },
    'Library Card': { # Preferred name
        'client_id': '7WxE9NUvTweka9Qbe4cO5LFJO3uDf8Ef9uhPacQi',
        'client_secret': 'IekRMuRAulipw8CC40BAkfvDLmscDDKR8Z6I7c3kCP9TDPVWuqAqwMIBTJaYoM306pajN85CvDkGZilT0QX0HbW1SjoRiRtq4jmtqFuXQ1n2hxD2lG827gFosgLXlEmV',
        'redirect_uri': 'http://127.0.0.1:8000/test-callback/',
        'scopes': 'openid profile identity',
    },
    'Transcript': { # Legal name
        'client_id': '4ykAdXmN1JByyERQP787rSM8Y31NyPeg5hgzmSfg',
        'client_secret': 'MoaEm22yCN2fNBhEfkLMwxZjDMLTic9f62uv26FPMsxhPKCknqahND5bZPeqaF03cyvYsILReSoxiG6L07vnKImgy3ykbFYKDvChMKQCeTxeoTNit0BwNGbUCdtPFMZv',
        'redirect_uri': 'http://127.0.0.1:8000/test-callback/',
        'scopes': 'openid identity affiliations:courses',
    },
}

def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def test_application(app_name, app_config):
    print(f"\n{'='*70}")
    print(f"Testing App: {app_name}")
    print(f"Requested Scopes: {app_config['scopes']}")
    print('='*70)
    
    code_verifier, code_challenge = generate_pkce_pair()
    
    auth_params = {
        'response_type': 'code',
        'client_id': app_config['client_id'],
        'redirect_uri': app_config['redirect_uri'],
        'scope': app_config['scopes'],
        'state': 'test123',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"{BASE_URL}/o/authorize/?{urlencode(auth_params)}"
    
    print(f"\n1. Open this URL in your browser:\n   {auth_url}\n")
    code = input("2. Paste the authorization code: ").strip()
    
    print("\n3. Exchanging code for token...")
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': app_config['redirect_uri'],
        'client_id': app_config['client_id'],
        'client_secret': app_config['client_secret'],
        'code_verifier': code_verifier
    }

    response = requests.post(f"{BASE_URL}/o/token/", data=token_data)
    
    if response.status_code != 200:
        print(f"   Token exchange failed! Error: {response.text[:18000]}")
        return
    
    tokens = response.json()
    print("   Tokens received!")
    
    print("\n4. Fetching user claims from /o/userinfo/...")
    headers = {'Authorization': f"Bearer {tokens['access_token']}"}
    userinfo = requests.get(f"{BASE_URL}/o/userinfo/", headers=headers).json()

    print(f"\nClaims Received:")
    print("-" * 70)
    print(json.dumps(userinfo, indent=2))
    print("-" * 70)
    
    # Summary Table
    print(f"Name:           {userinfo.get('name')}")
    print(f"Context:        {userinfo.get('context', 'N/A')}")
    
    # Identify which affiliation key to look for based on scopes
    aff_key = next((s for s in app_config['scopes'].split() if s.startswith('affiliations')), 'affiliations')
    aff_list = userinfo.get(aff_key, [])
    
    print(f"Affiliations ({aff_key}): {len(aff_list)}")
    for aff in aff_list:
        print(f"     - {aff.get('affiliation_type')}: {aff.get('affiliation_id')} ({aff.get('role_name')})")

def main():
    print("University OIDC Multi-App Tester")
    print("="*40)
    
    apps = list(APPLICATIONS.keys())
    for i, name in enumerate(apps, 1):
        print(f"{i}. {name}")
    
    try:
        choice = int(input("\nSelect an app to test (number): "))
        selected_app = apps[choice - 1]
        test_application(selected_app, APPLICATIONS[selected_app])
    except (ValueError, IndexError):
        print("Invalid selection. Exiting.")

if __name__ == "__main__":
    main()