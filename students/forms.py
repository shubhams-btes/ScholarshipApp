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
        exclude = ['exam_schedule', 'current_session', 'is_active']
        fields = ['name', 'email', 'password', 'mobile_number', 'stream', 'exam_schedule']
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
            'stream': forms.Select()
        }
        
    def clean_name(self):
        name = self.cleaned_data.get("name")

        # Allow only alphabets and spaces
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("College name must contain only alphabets.")

        return name
