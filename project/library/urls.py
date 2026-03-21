from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('callback/', views.callback, name='callback'),
    path('revoke/', views.revoke, name='revoke'),
]