from oauth2_provider.oauth2_validators import OAuth2Validator

class CustomOAuth2Validator(OAuth2Validator):
    """
    Custom validator to add university-specific claims to OIDC tokens.
    This adds claims to both the ID token and the /userinfo/ endpoint.
    """

    # Extend the standard OIDC scopes
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope.copy()
    
    oidc_claim_scope.update({
        'name': 'identity',
        'status': 'identity',
        'context': 'identity',
        'affiliations': 'affiliations',
        'affiliations:courses': 'affiliations:courses',
        'affiliations:clubs': 'affiliations:clubs',
        'affiliations:departments': 'affiliations:departments',
    })


    def get_additional_claims(self, request):
        user = request.user
        if user.is_anonymous:
            return {'sub': 'anonymous', 'error': 'Not authenticated'}
        
        # Institutional ID is required in every request
        identity = getattr(request.user, 'identity', None)

        if not identity:    # Admin has no identity
            return {
                'sub': request.user.username,
                'name': request.user.username,
                'status': 'ADMIN',
                'context': 'system'
            }

        # Basic claims
        claims = {
            'sub': identity.institutional_id,   # Unique ID required by OIDC
            'status': identity.status,
            'name': identity.full_name,
        }

        # Add the claims that are requested in scopes
        scopes = getattr(request, 'scopes', None)

        # Context-aware name selection.
        if 'profile' in scopes:
            # Get user's preferred name
            profile = getattr(identity, 'profile', None)

            if profile and profile.preferred_name:
                # Change the name claim
                claims['name'] = profile.preferred_name

        # Context-aware affiliation data

        if 'affiliations:courses' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations:courses', ['MOD', 'COURSE'], 'academic')
        
        elif 'affiliations:departments' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations:departments', ['DEPT'], 'academic')
        
        elif 'affiliations:clubs' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations:clubs', ['CLUB'], 'social')
        
        elif 'affiliations' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations', ['CLUB', 'MOD', 'COURSE', 'DEPT'], 'administrative')

        return claims
    

    def _add_affiliation_data(self, claims, identity, key, types, context):
        """Helper to safely filter and attach data"""
        affs = identity.affiliations.filter(
            affiliation_type__in=types, 
            is_active=True
        ).values('affiliation_type', 'affiliation_id', 'role_name')
        
        claims['context'] = context
        claims[key] = list(affs)