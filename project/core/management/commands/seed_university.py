import random
import re
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.factory import (
    IdentityFactory, AffiliationFactory, IdentityAffiliationFactory, ProfileFactory, UserFactory
)
from core.views import generate_email

class Command(BaseCommand):
    help = "Seeds the database with unique initial-based emails and clean User models."

    def handle(self, *args, **kwargs):
        self.stdout.write("🏗️  Starting University Seeding (Initial-based Emails)...")

        # Create the Entities
        cs_dept = AffiliationFactory(name="Department of Computer Science", uid="CS_DEPT", affiliation_type="DEPT")
        hr_dept = AffiliationFactory(name="Human Resources", uid="HR_DEPT", affiliation_type="DEPT")
        
        courses = [
            AffiliationFactory(name="Advanced Web Development", uid="COMP3001", affiliation_type="COURSE"),
            AffiliationFactory(name="Database Systems", uid="COMP2002", affiliation_type="COURSE"),
            AffiliationFactory(name="Intro to AI", uid="COMP4004", affiliation_type="COURSE"),
        ]

        # Create Staff (Professors, HR, Admins)
        staff_data = [
            ("Ada", "Lovelace", "STA", cs_dept), 
            ("Alan", "Turing", "STA", cs_dept),
            ("Grace", "Hopper", "STA", cs_dept),
            ("Hillary", "Rose", "STA", hr_dept), # HR Staff
        ]
        
        for first, last, status, dept in staff_data:
            email = generate_email(first, last, "@staff.uni.ac.uk")
            user = UserFactory(username=email, first_name="", last_name="")
            
            prof = IdentityFactory(user=user, legal_forenames=first, legal_surname=last, status=status)
            ProfileFactory(identity=prof)
            
            # Dept link
            IdentityAffiliationFactory(identity=prof, affiliation=dept, role_name="ST")
            
            # If they are CS staff, give them some teaching roles
            if dept == cs_dept:
                for course in random.sample(courses, 2):
                    IdentityAffiliationFactory(identity=prof, affiliation=course, role_name="IN")

        # Create Students
        student_count = 15
        for _ in range(student_count):
            temp_identity = IdentityFactory.build() 
            first, last = temp_identity.legal_forenames, temp_identity.legal_surname
            
            email = generate_email(first, last, "@uni.ac.uk")
            user = UserFactory(username=email, first_name="", last_name="")
            
            student = IdentityFactory(user=user, legal_forenames=first, legal_surname=last, status="STU")
            ProfileFactory(identity=student)
            
            # Random course enrollments (Many-to-Many)
            assigned_courses = random.sample(courses, k=random.randint(1, 3))
            for course in assigned_courses:
                IdentityAffiliationFactory(identity=student, affiliation=course, role_name="UG")

        self.stdout.write(self.style.SUCCESS(f"Seeding complete. All Users have clean name fields."))