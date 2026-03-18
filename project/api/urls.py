from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)


app_name = 'api'


urlpatterns = [
    path('me/', views.IdentityAPIView.as_view(), name='my_identity'),
    path('identity/<int:pk>/', views.IdentityAPIView.as_view(), name='identity'),
    path('display-name/', views.DisplayNameAPIView.as_view(), name='display_name'),
    path('preferred-name/', views.PreferredNameAPIView.as_view(), name='preferred_name'),
    path('roster/<str:affiliation_type>/<str:affiliation_id>/', views.RosterAPIView.as_view(), name='course_roster'),

    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]