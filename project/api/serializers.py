from rest_framework import serializers
from core.models import Identity, RolesAndAffiliations, Profile
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

    class Meta:
        model = Identity
        fields = ['display_name']

    def get_display_name(self, obj):
        # access the context passed from the view
        request_context = self.context.get('request_context')

        match request_context:
            case 'transcript':
                return obj.full_name

            case 'lms' | 'dashboard' | 'club-directory' | 'staff-directory':
                return getattr(obj.profile, 'preferred_name', obj.full_name) or obj.full_name

            case 'library-card':
                return obj.abbreviated_name
            
            case _:
                return obj.full_name


class IdentityMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ['institutional_id', 'full_name', 'status']
        read_only_fields = ['institutional_id', 'full_name', 'status']


class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        exclude = ['user']  # User pk should be a secret
    

class RolesAndAffiliationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolesAndAffiliations
        fields = '__all__'


class PreferredNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['preferred_name']