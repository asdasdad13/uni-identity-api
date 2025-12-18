from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Identity
from .serializers import IdentityNameSerializer

@api_view(['GET'])
def display_name(request, user_id):
    try:
        identity = Identity.objects.get(pk=user_id)
    except Identity.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # get the context from the request
    request_context = request.query_params.get('context', 'default')

    # pass context and identity values to serialiser
    serializer = IdentityNameSerializer(
        identity, 
        context={'request_context': request_context}
    )
    
    return Response(serializer.data)