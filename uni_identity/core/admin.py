from django.contrib import admin
from .models import Identity


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'institutional_id',
        'legal_forenames',
        'legal_surname',
        ]