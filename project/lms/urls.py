from django.urls import path
from . import views

app_name = 'lms'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('callback/', views.callback, name='callback'),
    path('view-roster/<str:roster_type>/<str:affiliation_id>/', views.view_roster, name='view_roster'),
    path('revoke/', views.revoke, name='revoke'),
]