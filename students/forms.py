import re
from django import forms
from .models import Student
from admin_panel.models import ExamSchedule


class StudentRegistrationForm(forms.ModelForm):
    # ── stream field REMOVED entirely ──

    class Meta:
        model = Student
        fields = [
            'name', 'email', 'mobile_number', 'roll_no', 'exam_schedule',
            'tenth_percentage', 'twelfth_percentage',
            'graduation_degree', 'graduation_percentage',
            'masters_degree', 'masters_percentage',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'mobile_number': forms.TextInput(attrs={'placeholder': 'Enter mobile number'}),
            'roll_no': forms.TextInput(attrs={'placeholder': 'Enter your roll number'}),
            'tenth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '10th %', 'step': '0.01', 'min': 0, 'max': 100}),
            'twelfth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '12th %', 'step': '0.01', 'min': 0, 'max': 100}),
            'graduation_degree': forms.Select(attrs={'class': 'form-select'}),
            'graduation_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Graduation %', 'step': '0.01', 'min': 0, 'max': 100}),
            'masters_degree': forms.Select(attrs={'class': 'form-select'}),
            'masters_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masters %', 'step': '0.01', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mandatory at form level (even though nullable at DB)
        for f in ['tenth_percentage', 'twelfth_percentage', 'graduation_degree', 'graduation_percentage']:
            self.fields[f].required = True
        # Masters optional
        self.fields['masters_degree'].required = False
        self.fields['masters_percentage'].required = False

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("Name must contain only alphabets.")
        return name

    def clean_roll_no(self):
        roll = self.cleaned_data.get("roll_no")
        if roll and not re.match(r'^[A-Za-z0-9]+$', roll):
            raise forms.ValidationError("Roll number must be alphanumeric.")
        return roll

    def clean(self):
        cleaned = super().clean()
        # Masters is all-or-nothing: degree and % must come together
        m_deg = cleaned.get('masters_degree')
        m_pct = cleaned.get('masters_percentage')
        if m_deg and not m_pct:
            self.add_error('masters_percentage', "Enter your Masters percentage.")
        if m_pct and not m_deg:
            self.add_error('masters_degree', "Select your Masters degree.")
        return cleaned