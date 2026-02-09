from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, BaseUserCreationForm

# hardcoded logins
from .models import Identity


def index(request):
    return render(request, 'index.html')