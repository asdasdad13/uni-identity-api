from django.contrib import admin
from .models import *
from .utils import log_admin_action
from django.contrib.admin.models import CHANGE, DELETION
from django.utils.html import format_html, mark_safe


class IdentityAffiliationInline(admin.TabularInline):
    model = IdentityAffiliation
    # Note: 'affiliation' is now a ForeignKey, so it shows a dropdown of Affiliation objects
    fields = ('affiliation', 'role_name', 'is_active')
    extra = 0

@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('name', 'uid', 'affiliation_type')
    list_filter = ('affiliation_type',)
    search_fields = ('name', 'uid')


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    inlines = [IdentityAffiliationInline]
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
        return super().get_queryset(request).prefetch_related('affiliations__affiliation')
        
    # Display roles and affiliations as a nicely formatted string in the admin list view
    @admin.display(description='Roles')
    def display_affiliations(self, obj):
        affs = obj.affiliations.all()

        if not affs:
            return '-'
        
        # Use format_html to include <br>
        html_items = [format_html('<strong>{}</strong>: {} ({})',
                                    aff.affiliation.affiliation_type,
                                    aff.affiliation_id,
                                    aff.role_name,
                                  )
                      for aff in affs]

        # Can use mark_safe since format_html guarantees sanitised input
        return mark_safe("<br>".join(html_items))


@admin.register(PendingAffiliation)
class PendingAffiliationAdmin(admin.ModelAdmin):
    list_display = ('identity', 'get_aff_type', 'get_aff_name', 'role_name')
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

    @admin.display(description="Type")
    def get_aff_type(self, obj):
        return obj.affiliation.get_affiliation_type_display()

    @admin.display(description="Affiliation Name")
    def get_aff_name(self, obj):
        return obj.affiliation.name


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('preferred_name',)