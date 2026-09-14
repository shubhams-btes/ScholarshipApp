import re
from django import forms
from .models import Student
from admin_panel.models import ExamSchedule


class StudentRegistrationForm(forms.ModelForm):
    STREAM_CHOICES = [
        ('BTECH', 'B.Tech'),
        ('MCA', 'MCA'),
    ]
    stream = forms.ChoiceField(
        choices=STREAM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Student
        fields = ['name', 'email', 'password', 'mobile_number', 'stream', 'roll_no', 'exam_schedule']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter your name'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email'
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Enter password'
            }),
            'mobile_number': forms.TextInput(attrs={
                'placeholder': 'Enter mobile number'
            }),
            'roll_no': forms.TextInput(attrs={'placeholder': 'Enter your roll number'}),
            'stream': forms.Select()
        }
        
    def clean_name(self):
        name = self.cleaned_data.get("name")

        # Allow only alphabets and spaces
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("College name must contain only alphabets.")

        return name
    
    def clean_roll_no(self):
        roll = self.cleaned_data.get("roll_no")
        if roll and not re.match(r'^[A-Za-z0-9]+$', roll):
            raise forms.ValidationError("Roll number must be alphanumeric.")
        return roll
