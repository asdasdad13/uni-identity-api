from django.shortcuts import render
from .views import *

def index(request):
    return render(request, 'index.html')

# Contextual switching
def home(request, id): # display legal and preferred name
    user = Identity.objects.get(id=id)
    context = request.GET.get('context', 'default')

    match context:
        case 'payroll':
            display_name = user.legal_name
        case 'lms':
            display_name = user.preferred_name
        case _:
            display_name = "Access Denied: Invalid Context"

    return render(request, 'home.html', {'name': display_name})