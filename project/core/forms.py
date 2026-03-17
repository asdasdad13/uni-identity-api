from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.models import User
from .models import RolesAndAffiliations, Profile


class DateInput(forms.DateInput):
    """HTML5 date picker."""
    input_type = 'date'


class StudentCreationForm(BaseUserCreationForm):
    # The institutional email address gets generated dynamically in Model
    legal_forenames = forms.CharField(max_length=200, label="Given Names / Forenames")
    legal_surname = forms.CharField(max_length=100, label="Family Name / Surname")
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = []
    
class StaffCreationForm(StudentCreationForm):
    class Meta(StudentCreationForm.Meta):   # Inherit same properties
        pass


class AffiliationRequestForm(forms.ModelForm):
    class Meta:
        model = RolesAndAffiliations
        fields = ['affiliation_type', 'role_name', 'affiliation_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Overwrite default ModelForm to have
        # adaptive role_name field depending on selected affiliation_type.

        # Check POST/GET data for AJAX call
        # Or use value from unbound form
        aff_type = self.data.get('affiliation_type') or self.initial.get('affiliation_type')

        self.fields['role_name'].choices = self.get_role_choices(aff_type)

    @staticmethod
    def get_role_choices(aff_type):
        match aff_type:
            case 'CLUB':
                return [('CM', 'Club Member'), ('PR', 'President')]
            case 'COURSE' | 'MOD':
                return [('UG', 'Undergraduate'), ('PG', 'Postgraduate')]
            case 'DEPT':
                return [('PF', 'Professor'), ('AD', 'Admin')]
            case _:
                return [('', '---Select Type First---')]