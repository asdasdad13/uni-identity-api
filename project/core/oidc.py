from oauth2_provider.oauth2_validators import OAuth2Validator

class CustomOAuth2Validator(OAuth2Validator):
    """
    Custom validator to add university-specific claims to OIDC tokens.
    This adds claims to both the ID token and the /userinfo/ endpoint.
    """

    # Extend the standard OIDC scopes
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update({
        # Format: Claim name -> Claim data
        # I.e. The app wants to read user's STATUS,
        # For that it has to read from user's IDENTITY.
        # App requests for IDENTITY scope.
        # So the 'status' claim gets mapped to 'identity'.
        
        'name': 'identity',

        'family_name': 'profile',
        'given_name': 'profile',
        'status': 'profile',

        'affiliations': 'affiliations',
        'affiliations:courses': 'affiliations:courses',
        'affiliations:clubs': 'affiliations:clubs',
        'affiliations:departments': 'affiliations:departments',
    })


    def get_additional_claims(self, request):
        user = request.user

        # Reject all logged out users.
        if user.is_anonymous:
            return {'sub': 'anonymous', 'error': 'Not authenticated'}
        
        # Institutional ID is required in every request
        identity = getattr(user, 'identity', None)

        if not identity:    # Admin has no identity
            return {
                'sub': user.username,
                'name': 'ADMIN',
                'username': user.username
            }

        # Basic claims
        claims = {
            'sub': identity.institutional_id,   # Unique ID required by OIDC
            'name': identity.full_name,
        }

        # Add the claims that are requested in scopes
        scopes = getattr(request, 'scopes', None)

        # Context-aware name selection.
        if 'profile' in scopes:
            # Get user's preferred name
            profile = getattr(identity, 'profile', None)

            # Get app name
            app: str = request.client.name.lower()

            # Return appropriate name format based on requesting app.
            # This it outlined in the design document,
            # basically, anything that isn't legal matters
            # like social directories should use alternative name formats.

            if profile and profile.preferred_name:
                match app:
                    case 'Library Card':
                        claims['name'] = profile.abbreviated_name

                    case _ :
                        claims['name'] = profile.preferred_name

                    # Apps pertaining to legal matters won't ask for profile
                    # and neither do they want preferred name info.

        # Context-aware affiliation data

        if 'affiliations:courses' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations:courses', ['MOD', 'COURSE'])
        
        elif 'affiliations:departments' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations:departments', ['DEPT'])
        
        elif 'affiliations:clubs' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations:clubs', ['CLUB'])
        
        elif 'affiliations' in scopes:
            self._add_affiliation_data(claims, identity, 'affiliations', ['CLUB', 'MOD', 'COURSE', 'DEPT'])

        return claims
    

    def _add_affiliation_data(self, claims, identity, key, types):
        """Helper to safely filter and attach data"""
        affs = identity.affiliations.filter(
            affiliation_type__in=types, 
            is_active=True
        ).values('affiliation_type', 'affiliation_id', 'role_name')
        
        claims[key] = list(affs)