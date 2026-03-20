from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, QueryDict
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView
from django.utils.safestring import mark_safe
from core.models import Identity, Profile, IdentityAffiliation
from django.urls import reverse_lazy
from django.conf import settings
from api.utils import get_token
from .forms import *
from .utils import generate_email
import requests
import datetime
import time

HOST_BASE_URL = settings.HOST_BASE_URL


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
    token = get_token(request)
    url = f"{HOST_BASE_URL}/api/me/"
    headers = {'Authorization': f"Bearer {token}", 'context': 'dashboard'}

    api_response = requests.get(url, headers=headers)
    api_response.raise_for_status()
    data = api_response.json()

    context = {
        'display_name': data.get('display_name', None),
        'full_name': data.get('full_name', None),
        'preferred_name': (data.get('profile') or {}).get('preferred_name'),

        'id': data.get('institutional_id', None),
        'email': data.get('email', None),
        'role_name': data.get('role_name', None),
        'status': data.get('status', None),
        'effective_date': data.get('effective_date', None),
        'date_of_birth': data.get('date_of_birth', None),
        'affiliations': data.get('affiliations', []),
    }

    return render(request, 'dashboard.html', context)


class BaseRegisterView(CreateView):
    """Base class to handle common Identity Provisioning logic."""
    success_url = reverse_lazy('core:dashboard')
    registration_status = None  # To be overridden by subclasses (e.g., 'STU' or 'STA')

    def form_valid(self, form):
        user = form.save(commit=False)  # Create object in memory
        legal_forenames = form.cleaned_data.get('legal_forenames')
        legal_surname = form.cleaned_data.get('legal_surname')
        
        generated_email = generate_email(legal_forenames, legal_surname, self.email_domain)
        # Attach new email to the db object to User
        user.username = generated_email
        user.save()

        # Create new Identity for this person
        identity = Identity.objects.create(
            user=user,
            legal_forenames=legal_forenames,
            legal_surname=legal_surname,
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
            )

        response = super().form_valid(form)
        # Log the user in immediately after registration
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
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
    model = IdentityAffiliation
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
    
    def form_invalid(self, form):
        if self.request.htmx:
            error_html = "".join([f'<div class="alert alert-danger">{err}</div>' 
                             for err in form.non_field_errors()])
            response = HttpResponse(mark_safe(error_html))
        
            # Tell HTMX to ignore #submit-btn and hit the error container instead
            response['HX-Retarget'] = '#affiliation-container'
            return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the user in so the 'clean' method can check for duplicates
        kwargs['initial'] = {'user': self.request.user}
        return kwargs

@login_required
def load_roles(request):
    """A fragment loaded by HTMX for adaptive dropdown in CreateAffiliationView.
    Triggers after an affiliation type has been selected by the user.
    """
    
    affiliation_type = request.GET.get('affiliation_type')

    # Get the specific data for this type
    entities = Affiliation.objects.filter(affiliation_type=affiliation_type)
    role_choices = IdentityAffiliation.ROLE_MAP.get(affiliation_type, [])

    # Return the "fragment" that contains BOTH dropdowns
    return render(request, 'partials/affiliation_options_update.html', {
        'entities': entities,
        'choices': role_choices
    })


@login_required
def get_roles(request):
    """View of enrolment status and information."""

    token = get_token(request)
    headers = {'Authorization': f"Bearer {token}"}
    url=f"{HOST_BASE_URL}/me/"
    
    # API call
    response = requests.get(url, headers=headers)
    
    affiliations = []
    if response.status_code == 200:
        affiliations = response.json().get('affiliations', [])

    return render(request, 'get_roles.html', {'affiliations': affiliations})


@login_required
def preferred_name(request):
    """HTMX partial to render read-only preferred name."""

    context = {
        'preferred_name': request.GET.get('preferred_name', None)
    }

    return render(request, 'partials/preferred_name.html', context)


@login_required
def edit_preferred_name(request):
    """HTMX partial to render a form for user to change their preferred name."""

    return render(request, 'partials/edit_preferred_name.html')


@require_http_methods(["PATCH"])
@login_required
def save_preferred_name(request):
    """HTMX partial that saves user's new preferred name from a PATCH request (edit_name)."""

    # Get value from request body to send to API
    data = QueryDict(request.body)
    new_name = data.get('preferred_name')
    token = get_token(request)

    # Call internal REST API to get data
    url = f"{HOST_BASE_URL}/api/preferred-name/"
    data = {'preferred_name': new_name}
    headers = {'Authorization': f"Bearer {token}"}

    api_response = requests.patch(url=url, json=data, headers=headers)

    # Re-render user info board with new name
    if api_response.status_code == 200:
        context = {'preferred_name': new_name}

        return render(request, 'partials/preferred_name.html', context)

    return HttpResponse(api_response)


# Admins can view and approve affiliation requests.

@staff_member_required
def affiliation_approvals(request):
    """Lists all pending (inactive) role/affiliation requests."""

    token = get_token(request)

    # Call internal REST API to get data
    url = f"{HOST_BASE_URL}/api/pending-affiliations/"
    headers = {'Authorization': f"Bearer {token}"}

    api_response = requests.get(url=url, headers=headers)

    # Re-render user info board with new name
    if api_response.status_code == 200:
        context = {
            'requests': api_response.json()
        }
    
    return render(request, 'admin/affiliation_approval.html', context)


@staff_member_required
def approve_affiliation(request, affiliation_id):
    """Action to approve or reject a specific request."""

    if not request.htmx:
        return HttpResponse(status=400)

    token = get_token(request)
    headers = {'Authorization': f"Bearer {token}"}
    # Get user's selected action from the form
    action = request.POST.get("action")
    
    url = f"{HOST_BASE_URL}/api/affiliations/{affiliation_id}/"

    if action == "approve":
        resp = requests.patch(url, data={'is_active': True}, headers=headers)
        if resp.status_code == 200:
            return render(request, 'admin/partials/approved.html')
        
    elif action == "reject":
        resp = requests.delete(url, headers=headers)
        if resp.status_code in [200, 204]:
            return render(request, 'admin/partials/rejected.html')
            
    return HttpResponse("API Error", status=500)