from django.contrib import admin
from .models import *
from .utils import log_admin_action
from django.contrib.admin.models import CHANGE, DELETION
from django.utils.html import format_html, mark_safe

class AffiliationsInline(admin.TabularInline):
    model = Affiliations
    fields = ('affiliation_id', 'affiliation_type', 'role_name', 'is_active')


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    inlines = [AffiliationsInline]
    list_display = (
        'id',
        'user__username',
        'institutional_id',
        'legal_forenames',
        'legal_surname',
        'full_name',
        'date_of_birth',

        'profile__preferred_name',

        'display_affiliations',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('affiliations')
    
    # Display roles and affiliations as a nicely formatted string in the admin list view
    @admin.display(description='Roles')
    def display_affiliations(self, obj):
        affs = obj.affiliations.all()

        if not affs:
            return '-'
        
        # Use format_html to include <br>
        html_items = [format_html('<strong>{}</strong>: {} ({})',
                                    aff.affiliation_type,
                                    aff.affiliation_id,
                                    aff.role_name,
                                  )
                      for aff in affs]

        # Can use mark_safe since format_html guarantees sanitised input
        return mark_safe("<br>".join(html_items))


@admin.register(PendingAffiliation)
class PendingAffiliationAdmin(admin.ModelAdmin):
    list_display = ('identity', 'affiliation_type', 'affiliation_id', 'role_name')
    list_filter = ('affiliation_type',)
    actions = ['approve_selected', 'reject_selected']

    def get_queryset(self, request):
        # Only show the requests that are NOT active
        return super().get_queryset(request).filter(is_active=False)
    
    # Remove the default "Delete selected option"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description="Approve selected requests")
    def approve_selected(self, request, queryset):
        for obj in queryset:
            obj.is_active = True
            obj.save()
            log_admin_action(request.user.id, [obj], CHANGE, "Approved affiliation.")

        self.message_user(request, f"Successfully approved {queryset.count()} requests.")

    @admin.action(description="Reject and delete selected requests")
    def reject_selected(self, request, queryset):
        count = queryset.count()
        for obj in queryset:
            log_admin_action(request.user.id, [obj], DELETION, "Rejected and deleted affiliation.")
            obj.delete()
        self.message_user(request, f"Successfully rejected and removed {count} requests.")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('preferred_name',)