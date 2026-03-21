from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('callback/', views.callback, name='callback'),
    path('view-roster/<str:roster_type>/<str:affiliation_id>/', views.view_roster, name='view_roster'),
    path('logout/', views.logout, name='logout'),
    path('logout-and-revoke/', views.logout_and_revoke, name='logout_and_revoke'),
]