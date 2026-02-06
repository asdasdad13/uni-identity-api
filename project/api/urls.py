from django.urls import path
from core import api_views

app_name = 'api'

urlpatterns = [
    path('identity/<int:user_id>/', api_views.full_identity, name='api_full_identity'),
    path('identity/<int:user_id>/name/', api_views.display_name, name='api_identity_name'),
]