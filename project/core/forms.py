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

    def clean(self):
        cleaned_data = super().clean()
        affiliation = cleaned_data.get('affiliation')
        
        # We need the user from the view to check existing affiliations
        user = self.initial.get('user') 
        
        if user and affiliation:
            if IdentityAffiliation.objects.filter(identity=user.identity, affiliation=affiliation).exists():
                raise forms.ValidationError("You have already joined or requested to join this affiliation.")
        
        return cleaned_data

    @staticmethod
    def get_role_choices(aff_type):
        return IdentityAffiliation.ROLE_MAP.get(aff_type, [])