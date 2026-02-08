from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'student'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='student/'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]