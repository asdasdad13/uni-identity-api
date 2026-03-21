from django.contrib import admin
from django.urls import include, path
from oauth2_provider import urls as oauth2_urls
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('o/', include(oauth2_urls)),
    path('lms/', include('lms.urls')),
    path('clubs/', include('clubs.urls')),
    path('staff/', include('staff.urls')),
    path('transcript/', include('transcript.urls')),
    path('library/', include('library.urls')),
    
    # DRF Spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
