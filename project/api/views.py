from rest_framework.decorators import api_view, permission_classes
from core.models import Identity, RolesAndAffiliations
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import *
from django.shortcuts import get_object_or_404
from .serializers import *
from .permissions import IsOwner, IsHRAdminOrOwner


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

    serializer = FullIdentitySerializer(target_identity)
    return Response(serializer.data)


# idk yet
@api_view(['GET'])
def display_name(request, user_id):
    """Endpoint to return the display name from an Identity object."""
    identity = get_object_or_404(Identity, pk=user_id)

    # get the context from the request
    request_context = request.query_params.get('context', 'default')

    # pass context and identity values to serialiser
    serializer = IdentityNameSerializer(identity, context={'request_context': request_context})
    
    return Response(serializer.data)






@api_view(['POST'])
def register(request):
    """
    POST /api/register/
    Body: {
        "username": "jd@uni.ac.uk",
        "password": "password123",
        "forename": "Jane",
        "surname": "Doe",
        "preferred_name": "J.D.",
        "date_of_birth": "2000-01-01"
    }
    """
    try:
        # Create user
        user = User.objects.create_user(
            username=request.data['username'],
            password=request.data['password'],
            email=request.data['username']
        )
        
        # Create identity
        identity = Identity.objects.create(
            user=user,
            legal_forenames=request.data['forename'],
            legal_surname=request.data['surname'],
            institutional_id=f"STU{datetime.now().year}{user.id:06d}U",
            status='STU',
            date_of_birth=request.data['date_of_birth'],
            effective_date=datetime.now()
        )
        
        # Create profile if preferred name provided
        if request.data.get('preferred_name'):
            Profile.objects.create(
                identity=identity,
                preferred_name=request.data['preferred_name'],
                name_type=request.data.get('name_type', 'Preferred name')
            )
        
        return Response({
            'message': 'User registered successfully',
            'institutional_id': identity.institutional_id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    GET /api/me/
    Returns authenticated user's profile
    """
    identity = request.user.identity
    profile = getattr(identity, 'profile', None)
    
    return Response({
        'institutional_id': identity.institutional_id,
        'legal_forename': identity.legal_forenames,
        'legal_surname': identity.legal_surname,
        'full_name': identity.full_name,
        'preferred_name': profile.preferred_name if profile else None,
        'name_type': profile.name_type if profile else None,
        'status': identity.status,
        'affiliations': list(identity.affiliations.filter(is_active=True).values())
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferred_name(request):
    """
    PUT /api/me/preferred-name/
    Body: {
        "preferred_name": "J.D.",
        "name_type": "Preferred name"
    }
    """
    identity = request.user.identity
    profile = getattr(identity, 'profile', None)
    
    if not profile:
        profile = Profile.objects.create(identity=identity)
    
    profile.preferred_name = request.data.get('preferred_name')
    profile.name_type = request.data.get('name_type', 'Preferred name')
    profile.save()
    
    return Response({
        'message': 'Preferred name updated',
        'preferred_name': profile.preferred_name
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_affiliation(request):
    """
    POST /api/affiliations/
    Body: {
        "affiliation_type": "COURSE",
        "role_name": "UG",
        "affiliation_id": "CS101"
    }
    """
    identity = request.user.identity
    
    affiliation = RolesAndAffiliations.objects.create(
        identity=identity,
        affiliation_type=request.data['affiliation_type'],
        role_name=request.data['role_name'],
        affiliation_id=request.data['affiliation_id'],
        is_active=False  # Pending approval
    )
    
    return Response({
        'message': 'Affiliation request submitted',
        'id': affiliation.id,
        'status': 'pending_approval'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_affiliations(request):
    """
    GET /api/me/affiliations/
    Returns user's affiliations
    """
    identity = request.user.identity
    affiliations = identity.affiliations.all()
    
    return Response({
        'affiliations': list(affiliations.values(
            'id', 'affiliation_type', 'role_name', 'affiliation_id', 'is_active'
        ))
    })