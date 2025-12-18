"""
URL configuration for uni_identity project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views, api_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='Student portal'),
    path('home/', views.home, name='home'),
    path('api/identity/<int:user_id>/name/', api_views.display_name, name='api_identity_name'),
]
