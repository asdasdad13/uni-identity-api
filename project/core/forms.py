from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.models import User
from .models import RolesAndAffiliations


class DateInput(forms.DateInput):
    """HTML5 date picker."""
    input_type = 'date'
    

class StudentCreationForm(BaseUserCreationForm):
    # The institutional email address gets generated dynamically in Model
    # Get student name
    forename = forms.CharField(
        max_length=200, 
        required=True,
        label="Given Names / Forenames",
        )
    surname = forms.CharField(
        max_length=100, 
        required=True,
        label="Family Name / Surname",
        )
    preferred_name = forms.CharField(max_length=200, required=False)
    name_type = forms.ChoiceField(
        choices=(
            ('--', '--'),
            ("Preferred name", "Preferred name"),
            ("Maiden Name", "Maiden Name"),
            ("Professional Alias", "Professional Alias"),
            ("Nickname", "Nickname"),
        ),
        required=False
    )
    date_of_birth = forms.DateField(required=True, widget=DateInput())

    class Meta:
        model = User
        fields = ('forename', 'surname', 'preferred_name',
                  'name_type', 'password1', 'password2', 'date_of_birth')

    def clean(self):
        cleaned_data = super().clean()
        
        preferred_name = cleaned_data.get('preferred_name')
        name_type = cleaned_data.get('name_type')

        # preferred_name exists but name_type is empty
        if preferred_name and not name_type:
            self.add_error('name_type', "Please specify name type.")
        
        return cleaned_data
    
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