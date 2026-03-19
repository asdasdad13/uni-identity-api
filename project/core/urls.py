from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Normal views
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('apply_affiliation/', views.CreateAffiliationView.as_view(), name='apply_affiliation'),
    path('affiliation_approvals/', views.affiliation_approvals, name='affiliation_approvals'),
    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('student/register/', views.StudentRegisterView.as_view(), name='register_student'),
    path('staff/register/', views.StaffRegisterView.as_view(), name='register_staff'),

    # HTMX partials
    path('roles/', views.get_roles, name='get_roles'),
    path('preferred-name/', views.preferred_name, name='preferred_name'),
    path('edit-preferred-name/', views.edit_preferred_name, name='edit_preferred_name'),
    path('save-preferred-name/', views.save_preferred_name, name='save_preferred_name'),
    path('load-roles/', views.load_roles, name='load_roles'),
    path('approvals/approve/<int:affiliation_id>/', views.approve_affiliation, name='approve_affiliation'),
]