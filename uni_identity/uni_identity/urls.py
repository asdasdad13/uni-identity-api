from django.contrib import admin
from django.urls import path
from core import views, api_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    # path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/login_js/', views.login_js, name='login_js'),
    path('accounts/login_jm/', views.login_jm, name='login_jm'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('api/identity/<int:user_id>/', api_views.full_identity, name='api_full_identity'),
    path('api/identity/<int:user_id>/name/', api_views.display_name, name='api_identity_name'),
]