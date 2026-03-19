from django.contrib.admin.models import CHANGE, DELETION
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from core.models import Identity, Affiliation
from .serializers import *
from .utils import log_admin_action


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

            # No Identity linked to user, like Admin.
            # Give some values at least.
            if not identity:
                user = request.user
                return Response({
                    "display_name": "Administrator",
                    "full_name": "Admin",
                    "institutional_id": "N/A",
                    "role_name": "Administrator",
                    "status": "ADM",
                    "email": getattr(user, 'email', user.username),
                    "affiliations": [],
                    "date_of_birth": None,
                    "effective_date": None,
                })
            
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
        # Get all members with this same affiliation
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
            "members": members.count(),
            "roster": serializer.data
        }, status=status.HTTP_200_OK)
    

class PendingAffiliationListAPIView(generics.ListAPIView):
    queryset = PendingAffiliation.objects.select_related('identity', 'affiliation')
    serializer_class = PendingAffiliationSerializer
    permission_classes = [IsAdminUser]


class IdentityAffiliationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IdentityAffiliation.objects.all()
    serializer_class = IdentityAffiliationSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        instance = serializer.save()
        
        log_admin_action(
            user_id=self.request.user.id, 
            queryset=[instance], 
            action_flag=CHANGE, 
            change_message="Approved affiliation."
        )
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        log_admin_action(
            user_id=self.request.user.id, 
            queryset=[instance], 
            action_flag=DELETION, 
            change_message="Rejected and deleted affiliation."
        )
        instance.delete()