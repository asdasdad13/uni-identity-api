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
    model = Profile
    fields = ['preferred_name', 'name_type']


class IdentityMeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Identity
        fields = ['institutional_id', 'full_name', 'display_name', 'status', 'profile']
        read_only_fields = ['institutional_id', 'full_name', 'display_name', 'status']

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

    def update(self, instance, validated_data):
        # Can update profile info
        profile_data = validated_data.pop('profile', None)
        instance.save()


        if profile_data:
            profile = instance.profile
            instance.preferred_name = validated_data.get('preferred_name', profile.preferred_name)
            instance.name_type = validated_data.get('name_type', profile.name_type)
            # @property abbreviated_name doesn't need
            # to be updated as it is dynamic.

            profile.save()
        
        return instance


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