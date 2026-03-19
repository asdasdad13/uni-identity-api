from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta, timezone
from django.contrib.admin.models import LogEntry


def log_admin_action(user_id, queryset, action_flag, change_message):
    LogEntry.objects.log_actions(
        user_id=user_id,
        queryset=queryset,
        action_flag=action_flag,
        change_message=change_message
    )
    

class ShortLivedAccessToken(AccessToken):
    """
    Super short-lived access token lasting 15 seconds.
    Use this to reduce attack surface, especially when making API request
    within a web view, and a long-lived access token is not necessary
    (e.g. making requests from terminal).
    """    

    lifetime = timedelta(seconds=15)


def get_token(request) -> str:
    """
    Retrieves a valid JWT from the session, or generates a new one
    if the existing one is missing or expired.
    """

    access_token = request.session.get('api_access_token')
    token_expiry = request.session.get('api_token_expiry')

    now = datetime.now(timezone.utc).timestamp()
    needs_new_token = True

    if access_token and token_expiry:
        if now < float(token_expiry) - 60:
            needs_new_token = False

    if needs_new_token:
        # Generate a new token for the logged-in user.
        token_obj = ShortLivedAccessToken.for_user(request.user)
        access_token = str(token_obj)
        
        # Update the session cache.
        request.session['api_access_token'] = access_token
        request.session['api_token_expiry'] = str(token_obj['exp'])
        
        # Mark the session as modified to ensure it saves.
        request.session.modified = True

    return access_token