from django.contrib import admin
from .models import *


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'institutional_id',
        'legal_forenames',
        'legal_surname',
        ]


class CustomUserAdmin(admin.ModelAdmin):
    list_select_related = ('identity', 'identity__profile')
    list_display = [
        'id',
        'username', # institutional email
        'legal_forenames',
        'legal_surname',
        'full_name',
        'preferred_name',
        'name_type',
        'date_of_birth',
        ]
    
    def legal_forenames(self, obj):
        return obj.identity.legal_forenames
    
    def legal_surname(self, obj):
        return obj.identity.legal_surname
    
    def full_name(self, obj):
        return obj.identity.full_name
    
    def preferred_name(self, obj):
        identity = getattr(obj, 'identity', None)
        if identity:
            profile = getattr(identity, 'profile', None)
            return getattr(profile, 'preferred_name', None)
        return None

    def name_type(self, obj):
        identity = getattr(obj, 'identity', None)
        if identity:
            profile = getattr(identity, 'profile', None)
            return getattr(profile, 'name_type', None)
        return None
    
    def date_of_birth(self, obj):
        return obj.identity.date_of_birth
    
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)