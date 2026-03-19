from django.db import models, transaction
from django.contrib.auth.models import User
import datetime

class IdentitySequence(models.Model):
    """Auxiliary table to help with generating unique sequence number for institutional_id."""
    year = models.PositiveIntegerField(unique=True)
    last_value = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.year}: {self.last_value}"


class Identity(models.Model):
    """Legal information about a person (staff/student/alumni) in the university."""

    user = models.OneToOneField(User, on_delete = models.CASCADE)
    institutional_id = models.CharField(
        max_length = 20,
        help_text = ("Automatically generated."),
        unique = True,
        editable = False,
        null=True,
    )
    legal_forenames = models.CharField(
        max_length = 200,
        help_text = ('All given names and middle names'
                    'exactly as they appear on the official ID.'),
        unique = False,
    )
    legal_surname = models.CharField(
        max_length = 100,
        help_text = 'The surname exactly as it appears on the official ID (passport).',
        unique = False,
    )

    effective_date = models.DateField(  # Null for non-students.
        help_text = 'The date a person started as their current status.',
        null=True,
    )

    status = models.CharField(
        help_text='Status of university member.',
        max_length = 20,
        default = None,
        choices = {
            "STU": "Active student",
            "STA": "Active staff",
            "ALU": "Alumni",
        }
    )

    date_of_birth = models.DateField(
        help_text="Date of birth.",
        null = True,
        blank = False,
        default = None,
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    @property
    def full_name(self):
        """Derived attribute from concatenating legal_forename and legal_surname."""
        return f"{self.legal_forenames} {self.legal_surname}"

    @staticmethod
    def calculate_check_digit(cohort_prefix: str, digits: str) -> str:
        WEIGHTS = {
            "A": [1, 1, 1, 1, 1, 1],
            "U": [0, 1, 3, 1, 2, 7],
            # More prefixes and weights can be added here in the future...
        }

        CHECK_DIGITS = "YXWURNMLJHEAB"
        
        # 1a. Remove the third digit.
        sliced_digits: str = digits[:2] + digits[3:]  # e.g. 123456 -> 12456

        # 1b. Convert to a usable format for scalar multiplication later.
        digits_list: list[int] = [int(digit) for digit in sliced_digits]

        # 2. Compute the weighted sum s = w1*d1 + ... + w6*d1
        weight: list[int] = WEIGHTS[cohort_prefix]
        prods: list[int] = [w*d for w, d in zip(weight, digits_list)]
        weighted_sum: int = sum(prods)

        # 3. Find the check digit corresponding to the remainder of weighted sum modulo 13
        return CHECK_DIGITS[weighted_sum % 13]

    def save(self, **kwargs):
        if not self.institutional_id:   # Generate only on creation of record
            # Generate a string like 'STU2025000001A'.
            year_prefix = str(datetime.datetime.now().year)

            with transaction.atomic():  # Ensure atomicity
                seq, _ = IdentitySequence.objects.select_for_update().get_or_create(
                    year=year_prefix
                )

                # Increment counter
                seq.last_value += 1
                seq.save()
                digits = f"{seq.last_value:06d}"     # 000001, 012345, 123456, ...

                check_digit = str(self.calculate_check_digit("U", digits))
                self.institutional_id = f"{self.status}{year_prefix}{digits}{check_digit}"
                        
        super().save(**kwargs)
    
    class Meta:
        verbose_name_plural = "Identities"

    def __str__(self):
        return self.full_name


class Profile(models.Model):
    """Non-critical information about a person's identity in the university."""

    identity = models.OneToOneField(
        Identity,
        on_delete = models.CASCADE,
        related_name = 'profile',
    )
    preferred_name = models.CharField(
        max_length = 200,
        help_text = 'Given by the user.',
        blank=True
    )

    @property
    def abbreviated_name(self):
        """John Thomas Smith -> J. T. Smith"""
        forenames = self.preferred_name or self.identity.legal_forenames

        initials = '. '.join(forename[0] for forename in forenames.split(' '))
        surname = self.identity.legal_surname
        return f"{initials}. {surname}"
    
    def __str__(self):
        return self.preferred_name
    

class Affiliation(models.Model):
    """The link between a User and a Course."""
    TYPE_CHOICES = {
        "CLUB": "Club",
        "COURSE": "Course",
        "MOD": "Module",
        "DEPT": "Department"
    }

    uid = models.CharField(
        max_length=100,
        help_text="Unique institutional ID",
        unique=True,
    )
    name = models.CharField(
        max_length = 100,
        unique = True,
    )
    affiliation_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )


class IdentityAffiliation(models.Model):
    """Junction table linking an Identity to an Affiliation."""

    identity = models.ForeignKey(
        Identity,
        on_delete = models.CASCADE,
        related_name = 'affiliations',
    )

    affiliation = models.ForeignKey(
        Affiliation, 
        on_delete=models.CASCADE,
        related_name='members'
    )

    ROLE_MAP = {
        'CLUB': [('CM', 'Club Member'), ('CP', 'President')],
        'COURSE': [('UG', 'Undergraduate'), ('PG', 'Postgraduate'), ('PF', 'Professor')],
        'MOD': [('UG', 'Undergraduate'), ('PG', 'Postgraduate'), ('PF', 'Professor')],
        'DEPT': [('PF', 'Professor'), ('AD', 'Admin')],
    }

    role_name = models.CharField(
        max_length=2,
        choices=[
            ('UG', 'Undergraduate'), ('PG', 'Postgraduate'), 
            ('CM', 'Club Member'), ('CP', 'Club President'), 
            ('PF', 'Professor'), ('AD', 'Admin'),
        ],
        help_text="Role within specified affiliation.",
    )

    AFFILIATION_TYPE_CHOICES = {
        "CLUB": "Club",
        "COURSE": "Course",
        "MOD": "Module",
        "DEPT": "Department"
    }

    is_active = models.BooleanField(
        default=False
    )

    class Meta:
        # Ensures a user can't join the same course twice!
        unique_together = ('identity', 'affiliation')

    def __str__(self):
        return f"{self.identity.full_name} in {self.affiliation.name}"
    
    
class PendingAffiliation(IdentityAffiliation):
    class Meta:
        proxy = True
        verbose_name = "Pending Approval"
        verbose_name_plural = "Pending Approvals"