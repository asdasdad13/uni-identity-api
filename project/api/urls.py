from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('identity/<int:user_id>/', views.full_identity, name='full_identity'),
    path('identity/<int:user_id>/name/', views.display_name, name='identity_name'),
    path('register/', views.register, name='register'),
    path('me/', views.get_profile, name='get_profile'),
    path('me/preferred-name/', views.update_preferred_name, name='update_preferred_name'),
    path('affiliations/', views.request_affiliation, name='request_affiliation'),
    path('me/affiliations/', views.get_affiliations, name='get_affiliations'),
]