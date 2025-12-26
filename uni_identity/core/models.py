from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Identity(models.Model):
    """Legal information about a person (staff/student/alumni) in the university."""

    user = models.OneToOneField(User, on_delete = models.CASCADE)
    institutional_id = models.CharField(
        max_length = 20,
        help_text = ("Automatically generated."),
        unique = True,
        editable = False,
        default = None,
    )
    legal_forenames = models.CharField(
        max_length = 200,
        help_text = ('All given names and middle names'
                    'exactly as they appear on the official ID.'),
        null = True,
        blank = False,
        unique = False,
    )
    legal_surname = models.CharField(
        max_length = 100,
        help_text = 'The surname exactly as it appears on the official ID (passport).',
        null = True,
        blank = False,
        unique = False,
    )

    effective_date = models.DateField(  # Null for non-students.
        help_text = 'The date a person started as their current status.',
        null = True,
        blank = True,
    )

    status = models.CharField(
        max_length = 20,
        null = True,
        blank = False,
        default = None,
        choices = {
            "STU": "Active student",
            "STA": "Active staff",
            "ALU": "Alumni",
        }
    )

    date_of_birth = models.DateField(
        null = True,
        blank = False,
        default = None,
    )

    @property
    def full_name(self):
        """Returns the person's full name."""
        return f"{self.legal_forenames} {self.legal_surname}"

    @staticmethod
    def calculate_check_digit(cohort_prefix: str, digits: str) -> str:
        WEIGHTS = {
            "A": [1, 1, 1, 1, 1, 1],
            "U": [0, 1, 3, 1, 2, 7],
            # More prefixes and weights can be added here in the future...
        }

        CHECK_DIGITS = {
            0: 'Y',     1: 'X',     2: 'W',
            3: 'U',     4: 'R',     5: 'N',
            6: 'M',     7: 'L',     8: 'J',
            9: 'H',     10: 'E',    11: 'A',
            12: 'B'
        }
        
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
        if not self.institutional_id:
            # Generate a string like 'STU2025000001A'.
            year_prefix: str = str(self.effective_date.year)
            
            # Count how many identities already exist with this year's cohort.
            count: int = Identity.objects.filter(institutional_id__contains=year_prefix).count()
            sequence_number: int = count + 1
            digits: str = f"{sequence_number:06d}"     # 000001, 012345, 123456, ...

            check_digit = str(self.calculate_check_digit("U", digits))
            self.institutional_id = f"{self.status}{year_prefix}{digits}{check_digit}"
        super().save(**kwargs)
    
    class Meta:
        verbose_name_plural = "Identities"


class Profile(models.Model):
    """Non-critical information about a person's identity in the university."""

    user = models.OneToOneField(Identity, on_delete = models.CASCADE)
    
    preferred_name = models.CharField(
        max_length = 200,
        help_text = 'Given by the user.',
        blank = False,
        null = True,
        unique = False,
    )
    @property
    def abbreviated_name(self):
        """John Thomas Smith -> J. T. Smith"""
        forenames = self.preferred_name or self.legal_forenames

        initials = ' '.join(forename[0] for forename in forenames.split(' '))
        surname = self.user.legal_surname
        return f"{initials} {surname}"