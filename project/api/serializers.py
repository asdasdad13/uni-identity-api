from rest_framework import serializers
from core.models import Identity, IdentityAffiliation, Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        if hasattr(user, 'identity'):
            token['institutional_id'] = user.identity.institutional_id
            token['status'] = user.identity.status
            
            if hasattr(user.identity, 'profile') and user.identity.profile.preferred_name:
                token['name'] = user.identity.profile.preferred_name
            else:
                token['name'] = user.identity.full_name

        return token
    

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['preferred_name', 'abbreviated_name']


class DisplayNameSerializer(serializers.ModelSerializer):
    # custom field that will change based on context
    display_name = serializers.SerializerMethodField()
    is_preferred = serializers.SerializerMethodField()
    is_abbreviated = serializers.SerializerMethodField()

    class Meta:
        model = Identity
        fields = ['display_name', 'is_preferred', 'is_abbreviated']

    def _get_context(self):
        """Helper to safely grab request context."""
        # Access the context passed from the view
        return self.context.get('request_context', 'default')

    def get_display_name(self, obj):
        request_context = self._get_context()

        match request_context:
            case 'transcript':
                return obj.full_name

            case 'lms' | 'dashboard' | 'club-directory' | 'staff-directory':
                # Return preferred if it exists, otherwise fallback to legal
                return getattr(obj.profile, 'preferred_name', obj.full_name) or obj.full_name

            case 'library-card':
                return obj.abbreviated_name
            
            case _:
                return obj.full_name
            
    # is_preferred and is_abbreviated only exist for showing off whether
    # the app correctly retrieved the preferred/abbreviated names, or
    # had to use a full name.
    def get_is_preferred(self, obj):
        """Check if the current context is displaying a preferred identity."""
        request_context = self._get_context()
        if request_context in ['lms', 'dashboard', 'club-directory', 'staff-directory']:
            # True only if a preferred name actually exists and isn't empty
            return bool(getattr(obj.profile, 'preferred_name', None))
        return False
            
    def get_is_abbreviated(self, obj):
        """Check if the current context is displaying an abbreviated identity."""
        return self._get_context() == 'library-card'

    
class AffiliationSerializer(serializers.ModelSerializer):
    affiliation_name = serializers.CharField(source='affiliation.name', read_only=True)
    affiliation_id = serializers.CharField(source='affiliation.uid', read_only=True)
    affiliation_type = serializers.CharField(source='affiliation.affiliation_type', read_only=True)
    role_name = serializers.CharField(source='get_role_name_display', read_only=True)

    class Meta:
        model = IdentityAffiliation
        fields = ('affiliation_type', 'affiliation_id', 'affiliation_name', 'role_name', 'is_active')

class IdentitySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.username', read_only=True)
    affiliations = serializers.SerializerMethodField()
    profile = ProfileSerializer(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Identity
        fields = [
            'institutional_id', 'full_name', 'date_of_birth', 'display_name', 'legal_forenames', 
            'legal_surname', 'status', 'effective_date', 'email', 'profile', 'affiliations'
        ]

    def get_affiliations(self, obj):
        """Returns only the active affiliations for this identity."""
        active_affs = obj.affiliations.filter(is_active=True)
        return AffiliationSerializer(active_affs, many=True).data

    def get_display_name(self, obj):
        """Return suitable display name for user."""
        serializer = DisplayNameSerializer(obj, context=self.context)
        return serializer.data.get('display_name')
    
    def to_representation(self, instance):
        # Get the standard representation
        data = super().to_representation(instance)
        
        # Check the context set in the view
        is_owner = self.context.get('is_owner', False)

        # If they aren't the owner, strip away the private stuff
        if not is_owner:
            private_fields = ['email', 'profile', 'affiliations', 'institutional_id']
            for field in private_fields:
                data.pop(field, None)
        print(f'IdentitySerializer: data={data}')
        return data
    

class IdentityAffiliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityAffiliation
        fields = ['id', 'is_active', 'role_name', 'affiliation', 'identity']


class PreferredNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['preferred_name']


class RosterMemberSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    institutional_id = serializers.ReadOnlyField(source='identity.institutional_id')
    role = serializers.CharField(source='get_role_name_display') # UG -> Undergraduate

    class Meta:
        model = IdentityAffiliation
        fields = ['institutional_id', 'display_name', 'role', 'is_active']

    def get_display_name(self, obj):
        """Return suitable display name for user."""
        serializer = DisplayNameSerializer(obj.identity, context=self.context)
        return serializer.data.get('display_name')