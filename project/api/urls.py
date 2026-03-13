from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)


app_name = 'api'


urlpatterns = [
    path('identity/<int:user_id>/', views.full_identity, name='full_identity'),
    path('me/', views.IdentityMeAPIView.as_view(), name='identity_me'),
    # path('register/', views.register, name='register'),
    # path('me/preferred-name/', views.update_preferred_name, name='update_preferred_name'),
    # path('affiliations/', views.request_affiliation, name='request_affiliation'),
    # path('me/affiliations/', views.get_affiliations, name='get_affiliations'),

    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]