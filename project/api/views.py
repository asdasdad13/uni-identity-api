from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404

from core.models import Identity, Affiliation
from .serializers import *


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class IdentityAPIView(APIView):
    """User's own identity."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    required_scopes = ['profile']

    def get(self, request, pk=None):
        if pk is None:  # Owner looking at own data
            identity = getattr(request.user, 'identity', None)
            is_owner = True
            
        else:   # Looking at someone else
            identity = get_object_or_404(Identity, pk=pk)
            is_owner = (request.user == identity.user)

        request_context = request.headers.get('context', None)

        serializer = IdentitySerializer(
            identity, 
            context={
                'request': request,
                'is_owner': is_owner or request.user.is_staff,
                'request_context': request_context,
            }
        )

        return Response(serializer.data)
    
    def patch(self, request):
        identity = getattr(request.user, 'identity', None)
        serializer = IdentitySerializer(identity, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors)
    

class PreferredNameAPIView(APIView):
    """A user's preferred name."""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    required_scopes = ['profile']
    
    def patch(self, request):
        profile, created = Profile.objects.get_or_create(identity=request.user.identity)
        serializer = PreferredNameSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors)
    

class DisplayNameAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    required_scopes = ['profile']

    def get(self, request):
        identity = request.user.identity
        serializer = DisplayNameSerializer(identity)
        return Response(serializer.data)

class RosterAPIView(APIView):
    """
    Returns a list of all active members (identities) for a 
    specific Affiliation (Course, Dept, etc.)
    """

    serializer_class = IdentitySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, affiliation_type, affiliation_id):
        # Verify the Affiliation exists
        group = get_object_or_404(
            Affiliation,
            affiliation_type=affiliation_type.upper(),
            uid=affiliation_id
        )

        # Query the junction table for active members
        members = IdentityAffiliation.objects.filter(
            affiliation=group,
            is_active=True
        ).select_related('identity') # Avoid the N+1 query problem.

        request_context = request.headers.get('context', None)

        serializer = RosterMemberSerializer(
            members,
            many=True,
            context={'request_context': request_context})   

        return Response({
            "affiliation_name": group.name,
            "type": group.get_affiliation_type_display(),
            "member_count": members.count(),
            "roster": serializer.data
        }, status=status.HTTP_200_OK)


class AffiliationAPIView(APIView):
    pass