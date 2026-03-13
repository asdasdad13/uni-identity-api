from rest_framework.decorators import api_view, permission_classes
from core.models import Identity, RolesAndAffiliations
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasScope
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import *
from .permissions import IsOwner, IsHRAdminOrOwner


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_affiliations(request, student_id):
    """
    GET /api/students/12345678/affiliations?context=academic
    """
    context = request.GET.get('context')
    
    affiliations = RolesAndAffiliations.objects.filter(
        identity__institutional_id=student_id,
        is_active=True
    )
    
    # Filter based on context parameter
    if context == 'academic':
        affiliations = affiliations.filter(
            affiliation_type__in=['COURSE', 'MOD', 'DEPT']
        )
    elif context == 'social':
        affiliations = affiliations.filter(affiliation_type='CLUB')
    
    return Response({
        'student_id': student_id,
        'context': context,
        'affiliations': RolesAndAffiliationsSerializer(affiliations, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsHRAdminOrOwner])
def full_identity(request, user_id):
    """Endpoint to return all attributes in an Identity object."""
    target_identity = get_object_or_404(Identity, pk=user_id)
    permission = IsHRAdminOrOwner()
    if not permission.has_object_permission(request, None, target_identity):
        return Response({"detail": "You do not have permission to view this record."}, status=403)

    serializer = IdentitySerializer(target_identity)
    return Response(serializer.data)


class IdentityMeAPIView(APIView):
    """
    REST API endpoint for the current user to read their identity.
    Protected by OAuth2 scopes.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    required_scopes = ['profile']

    def get(self, request):
        identity = request.user.identity
        serializer = IdentityMeSerializer(identity)
        return Response(serializer.data)