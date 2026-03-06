from oauth2_provider.views import ScopedProtectedResourceView

def get_custom_claims(user):
    """Add university-specific claims to ID token"""
    try:
        identity = user.identity
        profile = getattr(identity, 'profile', None)
        
        claims = {
            'institutional_id': identity.institutional_id,
            'status': identity.status,
            'legal_name': identity.full_name,
        }
        
        if profile:
            claims['preferred_name'] = profile.preferred_name
            claims['name_type'] = profile.name_type
        
        # Add active affiliations
        affiliations = identity.affiliations.filter(is_active=True).values(
            'affiliation_type', 'role_name', 'affiliation_id'
        )
        claims['affiliations'] = list(affiliations)
        
        return claims
    except:
        return {}