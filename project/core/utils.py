from django.contrib.admin.models import LogEntry
from .models import User
import re

def log_admin_action(user_id, queryset, action_flag, change_message):
    LogEntry.objects.log_actions(
        user_id=user_id,
        queryset=queryset,
        action_flag=action_flag,
        change_message=change_message
    )


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