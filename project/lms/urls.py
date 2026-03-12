from django.urls import path
from . import views

app_name = 'lms'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('callback/', views.callback, name='callback'),
    path('logout/', views.logout, name='logout'),
    path('logout-and-revoke/', views.logout_and_revoke, name='logout_and_revoke'),
]