import random
from django.core.management.base import BaseCommand
from core.factory import *
from core.utils import generate_email

class Command(BaseCommand):
    help = "Seeds the database with unique initial-based emails and clean User models."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting University Seeding")

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
            domain = "@staff.uni.ac.uk"
            email = generate_email(first, last, domain)
            
            # Create the User
            user = UserFactory(username=email, domain_val=domain)

            # Create the Identity
            prof = IdentityFactory(
                user=user, 
                legal_forenames=first, 
                legal_surname=last, 
                status=status
            )
            
            # Create the Profile
            ProfileFactory(identity=prof, preferred_name=f"Prof. {last}")
            
            # Create the Dept Link
            IdentityAffiliationFactory(identity=prof, affiliation=dept, role_name="STA")
            
            # If they are CS staff, give them some teaching roles
            if dept == cs_dept:
                for course in random.sample(courses, 2):
                    IdentityAffiliationFactory(identity=prof, affiliation=course, role_name="PF")

        # Create Students
        student_count = 15
        for _ in range(student_count):
            temp_identity = IdentityFactory.build() 
            first, last = temp_identity.legal_forenames, temp_identity.legal_surname
            domain = "@uni.ac.uk"

            email = generate_email(first, last, domain)
            user = UserFactory(username=email, domain_val=domain)
            
            student = IdentityFactory(user=user, legal_forenames=first, legal_surname=last, status="STU")
            ProfileFactory(identity=student)
            
            # Random course enrollments (Many-to-Many)
            assigned_courses = random.sample(courses, k=random.randint(1, 3))
            for course in assigned_courses:
                IdentityAffiliationFactory(identity=student, affiliation=course, role_name="UG")

        # Create 1 superuser
        admin_email = 'testadmin@staff.uni.ac.uk'
        if not User.objects.filter(username=admin_email).exists():
            User.objects.create_superuser(
                username=admin_email, 
                email=admin_email, 
                password='CsNq7heeeiz!Bm^5'
            )

        self.stdout.write(self.style.SUCCESS(f"Seeding complete."))