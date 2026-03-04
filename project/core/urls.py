from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apply_affiliation/', views.CreateAffiliationView.as_view(), name='apply_affiliation'),
    path('enrolment/', views.enrolment, name='enrolment'),
    path('affiliation_approvals/', views.affiliation_approvals, name='affiliation_approvals'),
    path('approvals/approve/<int:affiliation_id>/', views.approve_affiliation, name='approve_affiliation'),
    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('student/register/', views.StudentRegisterView.as_view(), name='register_student'),
    path('staff/register/', views.StaffRegisterView.as_view(), name='register_staff'),
]