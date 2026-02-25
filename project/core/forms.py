from django import forms
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.models import User


class DateInput(forms.DateInput):
    """HTML5 date picker."""
    input_type = 'date'
    

class StudentCreationForm(BaseUserCreationForm):
    # The institutional email address gets generated dynamically in Model
    # Get student name
    forename = forms.CharField(max_length=200, required=True)
    surname = forms.CharField(max_length=100, required=True)
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


# class CourseApplicationForm(BaseUserCreationForm):
#     # The institutional email address gets generated dynamically in Model
#     # Get student name
#     forename = forms.CharField(max_length=200, required=True)
#     surname = forms.CharField(max_length=100, required=True)
#     preferred_name = forms.CharField(max_length=200, required=False)
#     name_type = forms.ChoiceField(
#         choices=(
#             ('--', '--'),
#             ("Preferred name", "Preferred name"),
#             ("Maiden Name", "Maiden Name"),
#             ("Professional Alias", "Professional Alias"),
#             ("Nickname", "Nickname"),
#         ),
#         required=False
#     )
#     date_of_birth = forms.DateField(required=True, widget=DateInput())

#     class Meta:
#         model = User
#         fields = ('forename', 'surname', 'preferred_name',
#                   'name_type', 'password1', 'password2', 'date_of_birth')