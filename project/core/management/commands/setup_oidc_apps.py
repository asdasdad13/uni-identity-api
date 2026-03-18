import os
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Registers the OIDC applications using environment variables."

    def handle(self, *args, **kwargs):
        # 1. Ensure we have a system user to 'own' the apps (usually the first superuser)
        owner = User.objects.filter(is_superuser=True).first()
        if not owner:
            self.stdout.write(self.style.ERROR("Error: No superuser found. Create one first."))
            return

        # Define the apps and their specific requirements
        # Note: 'openid' and 'profile' are usually the default scopes
        apps_to_create = [
            {"name": "Library Card", "redirect": "http://localhost:8000/library/callback/ http://127.0.0.1:8000/library/callback/"},
            {"name": "LMS", "redirect": "http://localhost:8000/lms/callback/ http://127.0.0.1:8000/lms/callback/"},
            {"name": "Staff Directory", "redirect": "http://localhost:8000/staff/callback/ http://127.0.0.1:8000/staff/callback/"},
            {"name": "Club Directory", "redirect": "http://localhost:8000/clubs/callback/ http://127.0.0.1:8000/clubs/callback/"},
            {"name": "Transcript", "redirect": "http://localhost:8000/transcript/callback/ http://127.0.0.1:8000/transcript/callback/"},
        ]

        self.stdout.write("Registering OIDC Applications...")

        for app_data in apps_to_create:
            # Use update_or_create to prevent duplicates
            app, created = Application.objects.update_or_create(
                name=app_data['name'],
                defaults={
                    'user': owner,
                    'client_id': os.getenv(f"{app_data['name'].replace(' ', '_').upper()}_CLIENT_ID"),
                    'client_secret': os.getenv(f"{app_data['name'].replace(' ', '_').upper()}_CLIENT_SECRET"),
                    'client_type': Application.CLIENT_CONFIDENTIAL,
                    'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                    'redirect_uris': app_data['redirect'],
                    'algorithm': 'RS256',
                }
            )

            status = "Created" if created else "Updated"
            self.stdout.write(f"  - {app.name}: {status} (ID: {app.client_id[:8]}...)")

        self.stdout.write(self.style.SUCCESS("OIDC applications created."))