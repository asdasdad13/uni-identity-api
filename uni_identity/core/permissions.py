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

        if request.user.is_superuser:   # Admin is always allowed.
            return True
        
        if request.user.groups.filter(name='HR').exists():  # User is in HR group.
            return True
            
        if request.user.is_authenticated:   # User making request is the owner of the object to query.
            return obj.user == request.user