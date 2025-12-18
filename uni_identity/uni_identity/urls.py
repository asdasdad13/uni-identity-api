from django.contrib import admin
from django.urls import path
from core import views, api_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='Student portal'),
    path('home/', views.home, name='home'),
    path('api/identity/<int:user_id>/', api_views.full_identity, name='api_identity'),
    path('api/identity/<int:user_id>/name/', api_views.display_name, name='api_identity_name'),
]
