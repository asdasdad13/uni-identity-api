from .models import User
import re
from django.contrib.auth.views import redirect_to_login
from functools import wraps
from django.shortcuts import redirect


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


def oauth_required(app_name):
    """
    Decorator to require OAuth authorisation.
    User must be logged into IdP AND have authorized decorated app via OAuth.
    Redirects unauthorised users to login view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is logged into IdP
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            
            # User is logged in, check if they've authorised via OAuth
            if f'{app_name}_access_token' not in request.session:
                return redirect(f'{app_name}:login')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator