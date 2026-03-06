from django.contrib import admin
from django.urls import include, path
from oauth2_provider import urls as oauth2_urls
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('o/', include(oauth2_urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
