from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'identities'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('student/register/', views.StudentRegisterView.as_view(), name='register_student'),
    path('staff/register/', views.StaffRegisterView.as_view(), name='register_staff'),
]