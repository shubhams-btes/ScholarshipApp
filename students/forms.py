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
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_schedule': forms.Select(attrs={'class': 'form-select'}),
        }
