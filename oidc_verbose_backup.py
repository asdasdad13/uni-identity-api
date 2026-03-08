from oauth2_provider.oauth2_validators import OAuth2Validator
from django.db.models import Q
import logging
logger = logging.getLogger(__name__)


class CustomOAuth2Validator(OAuth2Validator):
    """
    Custom validator to add university-specific claims to OIDC tokens.
    This adds claims to both the ID token and the /userinfo/ endpoint.
    """

    def get_additional_claims(self, request):
        logger.info(f"Getting claims for user: {request.user.username}")
        logger.info(f"Requested scopes: {getattr(request, 'scopes', [])}")
        
        try:
            identity = request.user.identity

            # Get the OAuth Application making the request
            application = request.client
            
            # Basic claims
            claims = {
                'sub': identity.institutional_id,   # Unique ID required by OIDC
                'status': identity.status,
                'name': identity.full_name,
            }

            # Context-aware name selection.
            if 'profile' in scopes:
                profile = getattr(identity, 'profile', None)

                if profile and profile.preferred_name:
                    claims['name'] = profile.preferred_name

            # Add the claims that are requested in scopes
            scopes = getattr(request, 'scopes', [])

            if 'email' in scopes:
                claims['email'] = request.user.email

            # Context-aware affiliation and data
            affiliations = identity.affiliations.filter(is_active=True)

            affiliation_scopes = [
                {   
                    'requested_scope': 'affiliations:courses',
                    'affiliation_types': ['MOD', 'COURSE'],
                    'context': 'academic',
                },
                {   
                    'requested_scope': 'affiliations:departments',
                    'affiliation_types': ['DEPT'],
                    'context': 'academic',
                },
                {   
                    'requested_scope': 'affiliations:clubs',
                    'affiliation_types': ['CLUB'],
                    'context': 'social',
                },
                
            ]
            affiliation_scope_requested = any('affiliation' in scope for scope in scopes)

            if affiliation_scope_requested:

                if 'affiliations:courses' in scopes:    # LMS and Transcript will ask for these
                    affiliations = affiliations.filter(Q(affiliation_type='MOD') | Q(affiliation_type='COURSE'))
                    claims['context'] = 'academic'

                elif 'affiliations:clubs' in scopes:    # Club Directory
                    affiliations = affiliations.filter(affiliation_type='CLUB')
                    claims['context'] = 'social'
                    
                elif 'affiliations:departments' in scopes:  # Staff Directory
                    affiliations = affiliations.filter(affiliation_type='DEPT')
                    claims['context'] = 'social'
                
                else:
                    affiliations = affiliations.none()
                    claims['context'] = 'restricted'
                    logger.warning(f"Unknown application: {application.name}")




            if 'affiliations' in scopes:
                affiliations = identity.affiliations.filter(is_active=True)
                app_name = application.name.lower()

                # Admin
                elif 'admin' in app_name:
                    claims['context'] = 'administrative'

                # Unknown app - restrict
            
                # Convert to list for JSON
                claims['affiliations'] = list(affiliations.values(
                    'affiliation_type',
                    'affiliation_id'
                    'role_name',
                ))

            # Add metadata about which app is requesting
            claims['aud'] = application.client_id  # Audience claim

            logger.info(f"Claims generated with context: {claims.get('context', 'none')}")
            return claims

        except Exception as e:
            return {
                'sub': request.user.username,
                'error': str(e)
            }