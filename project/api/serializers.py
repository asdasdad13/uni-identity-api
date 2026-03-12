from rest_framework import serializers
from core.models import Identity, RolesAndAffiliations


class FullIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        exclude = ['user']  # User pk should be a secret?


class IdentityNameSerializer(serializers.ModelSerializer):
    # custom field that will change based on context
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Identity
        fields = ['display_name']

    def get_display_name(self, obj):
        # access the context passed from the view
        request_context = self.context.get('request_context')
        
        if request_context == 'payroll':
            # return Combined legal name
            return f"{obj.legal_forenames} {obj.legal_surname}"
        # other contexts
        return obj.preferred_name
    

# idk yet
class RolesAndAffiliationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolesAndAffiliations
        fields = '__all__'