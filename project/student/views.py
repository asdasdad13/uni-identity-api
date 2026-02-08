from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic.edit import CreateView
from django.contrib.auth.decorators import login_required
from .forms import *
from django.urls import reverse_lazy
from core.models import Identity, Profile
import datetime

import re


def index(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')
    else:
        return render(request, 'student/index.html')


def generate_email(first_name, last_name):
    """Based on student name initials."""
    base_prefix = f"{first_name[0]}{last_name[0]}".lower() # Jane Doe -> jd
    domain = "@edu.abc.uk"
    
    # Clean non-alphanumeric characters
    base_prefix = re.sub(r'[^a-zA-Z0-9]', '', base_prefix)
    
    email = f"{base_prefix}{domain}"
    counter = 1
    
    # Check uniqueness against the User model
    while User.objects.filter(username=email).exists():
        email = f"{base_prefix}{counter}{domain}"
        counter += 1
        
    return email


class RegisterView(CreateView):
    template_name = 'student/register_student.html'
    form_class = StudentCreationForm
    success_url = reverse_lazy('student:student_dashboard')

    def form_valid(self, form):
        user = form.save(commit=False)  # Create object in memory

        forename = form.cleaned_data.get('forename')
        surname = form.cleaned_data.get('surname')
        preferred_name = form.cleaned_data.get('preferred_name')
        date_of_birth = form.cleaned_data.get('date_of_birth')
        generated_email = generate_email(forename, surname)

        # Attach new email to the db object to User
        user.username = generated_email

        # Save the new User
        user.save()

        # Create new Identity for this student
        identity = Identity.objects.create(
            user=user,
            legal_forenames=forename,
            legal_surname=surname,
            status='STU',
            date_of_birth = date_of_birth,
            effective_date = datetime.datetime.now(),
            # Realistically speaking, effective date is determined by legal document handling
        )

        if preferred_name:
            name_type = form.cleaned_data.get('name_type')
            Profile.objects.create(
                identity=identity,
                preferred_name=preferred_name,
                name_type=name_type,
            )


        response = super().form_valid(form)
        # Log the user in immediately after registration
        login(self.request, self.object)

        return response
    

@login_required
def student_dashboard(request):
    # Get preferred name if it exists
    identity = Identity.objects.get(user=request.user)
    profile = Profile.objects.get(identity=identity)

    match profile:
        case None:
            preferred_name = identity.full_name
        case _:
            preferred_name = profile.preferred_name

    context = {
        'name': preferred_name,
    }
    return render(request, 'student/dashboard.html', context)