from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from .forms import *
from django.urls import reverse_lazy
from core.models import Identity, Profile, RolesAndAffiliations
import datetime
import time
import re
from .utils import log_admin_action
from django.contrib.admin.models import CHANGE, DELETION

# Authentication levels for views
def is_staff(user):
    return user.identity.status == 'STA'

def is_student(user):
    return user.identity.status == 'STU'


# View logic

def index(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    else:
        return render(request, 'index.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    else:
        return render(request, 'registration/register.html')
    

@login_required
def dashboard(request):
    try:
        identity = (Identity.objects
                    .select_related('profile')
                    .prefetch_related('affiliations')
                    .get(user=request.user))
        # Try to get profile, handle the case where it might not exist
        profile = getattr(identity, 'profile', None)
        affiliations = identity.affiliations.all()

        context = {
            'name': profile.preferred_name if profile else identity.full_name,
            'role': identity.get_status_display(),
            'status_code': identity.status,
            'id': identity.institutional_id,
            'affiliations': affiliations,
        }
    except Identity.DoesNotExist:
        # Fallback for superusers who might not have an Identity record,
        # e.g. admins
        context = {
            'name': request.user.username,
            'role': "Administrator",
            'status_code': "ADM",
            'id': "N/A",
        }

    return render(request, 'dashboard.html', context)


def generate_email(first_name, last_name, domain):
    """Based on user's name initials."""
    base_prefix = f"{first_name[0]}{last_name[0]}".lower() # Jane Doe -> jd
    
    # Clean non-alphanumeric characters
    base_prefix = re.sub(r'[^a-zA-Z0-9]', '', base_prefix)
    
    email = f"{base_prefix}{domain}"
    counter = 1
    
    # Check uniqueness against the User model
    while User.objects.filter(username=email).exists():
        email = f"{base_prefix}{counter}{domain}"
        counter += 1
        
    return email


class BaseRegisterView(CreateView):
    """Base class to handle common Identity Provisioning logic."""
    success_url = reverse_lazy('core:dashboard')
    registration_status = None  # To be overridden by subclasses (e.g., 'STU' or 'STA')

    def form_valid(self, form):
        user = form.save(commit=False)  # Create object in memory
        forename = form.cleaned_data.get('forename')
        surname = form.cleaned_data.get('surname')
        
        generated_email = generate_email(forename, surname, self.email_domain)
        # Attach new email to the db object to User
        user.username = generated_email
        user.save()

        # Create new Identity for this person
        identity = Identity.objects.create(
            user=user,
            legal_forenames=forename,
            legal_surname=surname,
            status=self.registration_status,  # Set dynamically by subclass
            date_of_birth=form.cleaned_data.get('date_of_birth'),
            effective_date=datetime.datetime.now(),
            # Realistically speaking, effective date is determined by legal document handling
        )

        # Create new Profile for this person
        preferred_name = form.cleaned_data.get('preferred_name')
        if preferred_name:
            Profile.objects.create(
                identity=identity,
                preferred_name=preferred_name,
                name_type=form.cleaned_data.get('name_type'),
            )

        response = super().form_valid(form)
        # Log the user in immediately after registration
        login(self.request, self.object)
        return response


class StudentRegisterView(BaseRegisterView):
    template_name = 'student/register.html'
    form_class = StudentCreationForm
    registration_status = 'STU'
    email_domain = "@uni.ac.uk"


class StaffRegisterView(BaseRegisterView):
    template_name = 'staff/register.html'
    form_class = StaffCreationForm
    registration_status = 'STA'
    email_domain = "@staff.uni.ac.uk"


class CreateAffiliationView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """User sends application form to be registered
    as an undergraduate in some module. This simulates official
    student applications, but there isn't an office for this
    project.
    """

    # Handles GET
    model = RolesAndAffiliations
    form_class = AffiliationRequestForm
    template_name = 'request_affiliation.html'

    def test_func(self):
        return is_student(self.request.user) or is_staff(self.request.user)

    # Handles POST
    def form_valid(self, form):
        time.sleep(1)   # Artificial delay
        self.object = form.save(commit=False)
        self.object.identity = self.request.user.identity

        self.object.is_active=False     # Simulates "Pending Approval"
        self.object.save()

        # If HTMX request, return a fragment instead of redirect
        if self.request.htmx:
            return render(self.request, 'partials/submission_success.html')

        return super().form_valid(form)
    

def ajax_load_roles(request):
    """A fragment loaded by HTMX for adaptive dropdown in CreateAffiliationView.
    Triggers after an affiliation type has been selected by the user.
    """
    # Get user's selection
    affiliation_type = request.GET.get('affiliation_type')

    # Update role_name options in view of form
    choices = AffiliationRequestForm.get_role_choices(affiliation_type)

    return render(request, 'partials/role_dropdown_options.html', {'choices': choices})


@user_passes_test(is_student)
def enrolment(request):
    """Student view of enrolment status and information."""
    affiliations = (RolesAndAffiliations.objects
          .filter(identity__user=request.user)
          .values('affiliation_id', 'affiliation_type'))
    context = {
        'affiliations': affiliations
    }

    return render(request, 'student/enrolment.html', context)


# Admins can view and approve affiliation requests 
@staff_member_required
def affiliation_approvals(request):
    """Lists all pending (inactive) role/affiliation requests."""
    pending_requests = RolesAndAffiliations.objects.filter(is_active=False)

    return render(request, 'admin/affiliation_approval.html', {
        'requests': pending_requests
    })


@staff_member_required
def approve_affiliation(request, affiliation_id):
    """Action to set a specific affiliation to active."""
    if request.htmx:
        affiliation = get_object_or_404(RolesAndAffiliations, id=affiliation_id)

        match request.POST.get("action"):
            case "approve":
                affiliation.is_active = True
                affiliation.save()

                log_admin_action(request.user.id, [affiliation], CHANGE, "Approved affiliation.")

                return render(request, 'admin/partials/approved.html')
            
            case "reject":
                log_admin_action(request.user.id, [affiliation], DELETION, "Rejected and deleted affiliation.")

                affiliation.delete()
                return render(request, 'admin/partials/rejected.html')

def test_callback_view(request):
    code = request.GET.get('code')
    return render(request, 'oauth/test_callback.html', {
        'application': 'Library Card',
        'code': code,
    })