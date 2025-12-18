from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import *
from .serializers import *
from .permissions import *

# The default permission for all endpoints is authenticated users only. No public viewing is allowed.

@api_view(['GET'])
@permission_classes([IsHRAdminOrOwner])
def full_identity(request, user_id):
    target_identity = get_object_or_404(Identity, pk=user_id)
    permission = IsHRAdminOrOwner()
    if not permission.has_object_permission(request, None, target_identity):
        return Response({"detail": "You do not have permission to view this record."}, status=403)

    serializer = FullIdentitySerializer(target_identity)
    return Response(serializer.data)

@api_view(['GET'])
def display_name(request, user_id):
    identity = get_object_or_404(Identity, pk=user_id)

    # get the context from the request
    request_context = request.query_params.get('context', 'default')

    # pass context and identity values to serialiser
    serializer = IdentityNameSerializer(identity, context={'request_context': request_context})
    
    return Response(serializer.data)