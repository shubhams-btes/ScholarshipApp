from django import forms
from tests.models import Question
from .models import College, CollegeOfficial, ExamSchedule
from django.core.exceptions import ValidationError
import re

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'category',
            'question_text',
            'option_1',
            'option_2',
            'option_3',
            'option_4',
            'correct_option'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'required': True}),
            'option_1': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'option_2': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'option_3': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'option_4': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'correct_option': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        opt1 = cleaned_data.get("option_1")
        opt2 = cleaned_data.get("option_2")
        opt3 = cleaned_data.get("option_3")
        opt4 = cleaned_data.get("option_4")
        correct = cleaned_data.get("correct_option")

        # Ensure first 2 options exist
        if not opt1 or not opt2:
            raise ValidationError("Option 1 and Option 2 are required.")

        # Ensure correct option matches a filled option
        options_map = {
            1: opt1,
            2: opt2,
            3: opt3,
            4: opt4
        }
        if correct not in options_map or not options_map[correct]:
            raise ValidationError("Correct option must correspond to a filled option.")

class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control','pattern': '[A-Za-z ]+',
        'title': 'Only alphabets allowed.'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")

        # Allow only alphabets and spaces
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("College name must contain only alphabets.")

        return name

class CollegeOfficialForm(forms.ModelForm):
    class Meta:
        model = CollegeOfficial
        exclude = ['college']  # Important: exclude college
        fields = ['name', 'email', 'is_active']  # Exclude 'college'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control','pattern': '[A-Za-z ]+',
        'title': 'Only alphabets allowed.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
    def clean_name(self):
        name = self.cleaned_data.get("name")

        # Allow only alphabets and spaces
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("College name must contain only alphabets.")

        return name

class CollegeOfficialEditForm(forms.ModelForm):
    class Meta:
        model = CollegeOfficial
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control','pattern': '[A-Za-z ]+',
        'title': 'Only alphabets allowed.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
    def clean_name(self):
        name = self.cleaned_data.get("name")

        # Allow only alphabets and spaces
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("College name must contain only alphabets.")

        return name

class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = ['college', 'quiz_date', 'is_active']
        widgets = {
            'college': forms.Select(attrs={'class': 'form-select'}),
            'quiz_date': forms.DateInput(attrs={'class': 'form-control datetimepicker', 'placeholder': 'Select Date & Time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
