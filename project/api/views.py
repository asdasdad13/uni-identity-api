from rest_framework.decorators import api_view, permission_classes
from core.models import Identity
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import *
from rest_framework.generics import ListAPIView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class IdentityAPIView(APIView):
    """User's own identity."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    required_scopes = ['profile']

    def get(self, request, pk=None):
        if pk is None:  # Owner looking at own data
            try:
                instance = Identity.objects.get(user=request.user)
                is_owner = True
            except Identity.DoesNotExist:
                return Response({"error": "Identity not found"}, status=404)
            
        else:   # Looking at someone else
            instance = get_object_or_404(Identity, pk=pk)
            is_owner = (request.user == instance.user)

        request_context = request.headers.get('context', 'default')

        serializer = IdentitySerializer(
            instance, 
            context={
                'request': request,
                'is_owner': is_owner or request.user.is_staff,
                'request_context': request_context
            }
        )

        return Response(serializer.data)
    
    def patch(self, request):
        identity = request.user.identity
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

class BaseRosterAPIView(ListAPIView):
    serializer_class = IdentitySerializer
    permission_classes = [IsAuthenticated]
    affiliation_type = None

    def get_queryset(self):
        target_id = self.kwargs.get('affiliation_id')

        # Non-existent ID or ID has no affiliations yet
        if not target_id or not self.affiliation_type:
            return Identity.objects.none()
            
        # Filter identities that have an active affiliation type with this ID
        return Identity.objects.filter(
            affiliations__affiliation_id=target_id,
            affiliations__affiliation_type=self.affiliation_type,
            affiliations__is_active=True,
        ).distinct()

    def get_serializer_context(self):
        # Since this is a list of OTHER people,
        # is_owner will naturally be False for everyone except the requester.
        context = super().get_serializer_context()
        context['request_context'] = 'lms'
        context['is_owner'] = False 
        return context
    

class CourseRosterAPIView(BaseRosterAPIView):
    affiliation_type = 'COURSE'


class ModuleRosterAPIView(BaseRosterAPIView):
    affiliation_type = 'MOD'