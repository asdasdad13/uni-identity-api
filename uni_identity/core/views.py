from django.shortcuts import render, get_object_or_404, redirect
from .views import *
from django.contrib.auth.decorators import login_required
# hardcoded logins
from .models import *
from django.contrib.auth import login, authenticate

def index(request):
    return render(request, 'index.html')

def login_js(request):
    """
    PROTOTYPE USE ONLY, VERY UNSAFE
    """ 
    user = User.objects.get(username='js')
    login(request, user)

    return redirect('index')

def login_jm(request):
    """
    PROTOTYPE USE ONLY, VERY UNSAFE
    """
    user = User.objects.get(username='jm')
    login(request, user)

    return redirect('index')

@login_required
def home(request): # sample page display legal and preferred name
    try:
        user_identity = request.user.identity  
    except Identity.DoesNotExist:
        # User exists but hasn't had an Identity created yet
        return render(request, 'error.html', {'message': 'Identity profile not found.'})

    context = request.GET.get('context', 'default')

    match context:
        case 'payroll':
            display_name = user_identity.legal_name
        case 'lms':
            display_name = user_identity.preferred_name
        case _:
            display_name = f"Welcome, {user_identity.preferred_name}. Please select a context."

    return render(request, 'home.html', {'name': display_name})