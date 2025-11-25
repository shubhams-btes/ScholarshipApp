from django import forms
from tests.models import Question
from .models import College, CollegeOfficial, ExamSchedule
from django.forms import modelformset_factory
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
            'category': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'option_1': forms.TextInput(attrs={'class': 'form-control'}),
            'option_2': forms.TextInput(attrs={'class': 'form-control'}),
            'option_3': forms.TextInput(attrs={'class': 'form-control'}),
            'option_4': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_option': forms.Select(attrs={'class': 'form-select'}),
        }

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
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CollegeOfficialEditForm(forms.ModelForm):
    class Meta:
        model = CollegeOfficial
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = ['college', 'quiz_date', 'is_active']
        widgets = {
            'college': forms.Select(attrs={'class': 'form-select'}),
            'quiz_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
