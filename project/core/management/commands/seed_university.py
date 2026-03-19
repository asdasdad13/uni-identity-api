import random
from django.core.management.base import BaseCommand
from core.factory import *
from core.utils import generate_email

class Command(BaseCommand):
    help = "Seeds the database with User, Identity, Profile, Affiliation, IdentityAffiliation models."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting University Seeding")

        # Departments
        cs_dept = AffiliationFactory(name="Department of Computer Science", uid="CS_DEPT", affiliation_type="DEPT")
        hr_dept = AffiliationFactory(name="Human Resources", uid="HR_DEPT", affiliation_type="DEPT")
        
        # Courses
        courses = [
            AffiliationFactory(name="BSc Computer Science", uid="CS_BSC", affiliation_type="COURSE"),
            AffiliationFactory(name="MSc Data Science", uid="DS_MSC", affiliation_type="COURSE"),
        ]

        # Modules (The specific units within courses)
        modules = [
            AffiliationFactory(name="Advanced Web Development", uid="COMP3001", affiliation_type="MOD"),
            AffiliationFactory(name="Database Systems", uid="COMP2002", affiliation_type="MOD"),
            AffiliationFactory(name="Intro to AI", uid="COMP4004", affiliation_type="MOD"),
            AffiliationFactory(name="Software Engineering", uid="COMP1005", affiliation_type="MOD"),
        ]

        # Clubs
        clubs = [
            AffiliationFactory(name="Chess Club", uid="CLUB_CHESS", affiliation_type="CLUB"),
            AffiliationFactory(name="Hackathon Society", uid="CLUB_HACK", affiliation_type="CLUB"),
            AffiliationFactory(name="E-Sports Team", uid="CLUB_ESPORT", affiliation_type="CLUB"),
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
            
            # Enroll in 1 Course
            IdentityAffiliationFactory(identity=student, affiliation=random.choice(courses), role_name="UG")
            
            # Enroll in 2-3 Modules
            assigned_mods = random.sample(modules, k=random.randint(2, 3))
            for mod in assigned_mods:
                IdentityAffiliationFactory(identity=student, affiliation=mod, role_name="UG")

            # Join 1-2 Clubs
            assigned_clubs = random.sample(clubs, k=random.randint(1, 2))
            for club in assigned_clubs:
                IdentityAffiliationFactory(identity=student, affiliation=club, role_name="CM")

        # Create 1 known student
        u1 = User.objects.get(pk=student_count)
        u1.username = 'teststudent@uni.ac.uk'
        u1.save()

        i1 = Identity.objects.get(user=u1)
        i1.legal_forenames = 'Christopher'
        i1.legal_surname = 'Burton'
        i1.save()

        p1 = Profile.objects.get(identity=i1)
        p1.preferred_name = 'Chrissie'
        p1.save()

        # Create 1 known staff
        u2 = User.objects.get(pk=len(staff_data))
        u2.username = 'teststaff@staff.uni.ac.uk'
        u2.save()

        i2 = Identity.objects.get(user=u1)
        i2.legal_forenames = 'Alan'
        i2.legal_surname = 'Turing'
        i2.save()

        p2 = Profile.objects.get(identity=i1)
        p2.preferred_name = 'Prof. Turing'
        p2.save()

        # Create 1 known superuser
        admin_email = 'testadmin@staff.uni.ac.uk'
        if not User.objects.filter(username=admin_email).exists():
            User.objects.create_superuser(
                username=admin_email, 
                email=admin_email, 
                password='CsNq7heeeiz!Bm^5'
            )

        self.stdout.write(self.style.SUCCESS(f"Seeding complete."))