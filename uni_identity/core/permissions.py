from rest_framework import permissions

class IsOwner():
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return obj.user == request.user

class IsHRAdminOrOwner(permissions.BasePermission):
    """
    Custom permission to only allow HR, Admins, or the owner to see sensitive data.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        print(f"request.user = {request.user}")
        print(f"obj.user = {obj.user}")
        # admin/superuser always allowed
        if request.user.is_superuser:
            return True
        
        # check for HR group
        if request.user.groups.filter(name='HR').exists():
            return True
            
        # check if the identity belongs to the logged-in user
        if request.user.is_authenticated:
            return obj.user == request.user