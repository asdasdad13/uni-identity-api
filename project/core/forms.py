from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.models import User
from .models import Affiliation, IdentityAffiliation


class DateInput(forms.DateInput):
    """HTML5 date picker."""
    input_type = 'date'


class StudentCreationForm(BaseUserCreationForm):
    # The institutional email address gets generated dynamically in Model
    legal_forenames = forms.CharField(max_length=200, label="Given Names / Forenames")
    legal_surname = forms.CharField(max_length=100, label="Family Name / Surname")
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    preferred_name = forms.CharField(
        max_length=200, 
        required=False, 
        label="Preferred Name (Optional)",
        help_text="How you would like to be addressed in email correspondance and casual settings."
    )

    class Meta:
        model = User
        fields = []
    

class StaffCreationForm(StudentCreationForm):
    class Meta(StudentCreationForm.Meta):   # Inherit same properties
        pass


class AffiliationRequestForm(forms.ModelForm):
    affiliation_type = forms.ChoiceField(
        choices=Affiliation.TYPE_CHOICES,
        label="Type of Association"
    )

    class Meta:
        model = IdentityAffiliation
        fields = ['affiliation', 'role_name']
        labels = {
            'affiliation_type': 'Club / Course / Module / Department Name',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the selected type from the data (for HTMX) or the instance
        aff_type = self.data.get('affiliation_type') or self.initial.get('affiliation_type')

        # Filter the 'affiliation' choices based on the type selected
        if aff_type:
            self.fields['affiliation'].queryset = Affiliation.objects.filter(affiliation_type=aff_type)
            self.fields['role_name'].choices = IdentityAffiliation.ROLE_MAP.get(aff_type, [])
        
        else:
            # Set the dynamic roles based on the junction table's ROLE_MAP
            self.fields['affiliation'].queryset = Affiliation.objects.none()
            self.fields['role_name'].choices = []

    @staticmethod
    def get_role_choices(aff_type):
        return IdentityAffiliation.ROLE_MAP.get(aff_type, [])