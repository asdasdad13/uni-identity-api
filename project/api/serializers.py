from rest_framework import serializers
from core.models import Identity, RolesAndAffiliations
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from oauth2_provider.contrib.rest_framework import TokenHasScope


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
    

class IdentityMeSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Identity
        fields = ['institutional_id', 'display_name', 'status']

    def get_display_name(self, obj):
        """
        Logic: Use preferred_name if available, 
        else fall back to the legal full_name.
        """
        # Check if the related profile exists and has a preferred_name
        if hasattr(obj, 'profile') and obj.profile.preferred_name:
            return obj.profile.preferred_name
        
        # Fallback to the Identity model's full_name
        return obj.full_name


class IdentitySerializer(serializers.ModelSerializer):
    preferred_name = serializers.CharField(source='profile.preferred_name', read_only=True)
    abbreviated_name = serializers.CharField(source='profile.abbreviated_name', read_only=True)
    
    class Meta:
        model = Identity
        exclude = ['user']  # User pk should be a secret


class NameSerializer(serializers.ModelSerializer):
    # custom field that will change based on context
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Identity
        fields = ['display_name']

    def get_display_name(self, obj):
        # access the context passed from the view
        request_context = self.context.get('request_context')

        match request_context:
            case 'transcript':
                return f"{obj.full_name}"

            case 'lms' | 'dashboard' | 'club-directory' | 'staff-directory':
                return obj.profile.preferred_name

            case 'library-card':
                return obj.abbreviated_name
    

class RolesAndAffiliationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolesAndAffiliations
        fields = '__all__'