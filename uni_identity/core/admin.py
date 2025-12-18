from django.contrib import admin
from .models import Identity

@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = ['legal_forenames', 'legal_surname', 'preferred_name']