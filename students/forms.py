import re
from django import forms
from .models import Student
from admin_panel.models import ExamSchedule
from decimal import Decimal, InvalidOperation

CGPA_PCT_CHOICES = [('PCT', 'Percentage'), ('CGPA', 'CGPA')]


class StudentRegistrationForm(forms.ModelForm):

    # ── CGPA/% type dropdowns — form-only, drive conversion, not stored ──
    tenth_type = forms.ChoiceField(
        choices=CGPA_PCT_CHOICES, initial='PCT',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    twelfth_type = forms.ChoiceField(
        choices=CGPA_PCT_CHOICES, initial='PCT',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    graduation_type = forms.ChoiceField(
        choices=CGPA_PCT_CHOICES, initial='PCT',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    masters_type = forms.ChoiceField(
        choices=CGPA_PCT_CHOICES, initial='PCT', required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

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
            # NOTE: max removed from % inputs — a CGPA value (≤10) is valid here now,
            # so the HTML max=100 is fine, but min=0 stays. Step allows decimals.
            'tenth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 85 or 8.5', 'step': '0.01', 'min': 0}),
            'twelfth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 85 or 8.5', 'step': '0.01', 'min': 0}),
            'graduation_degree': forms.Select(attrs={'class': 'form-select'}),
            'graduation_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 85 or 8.5', 'step': '0.01', 'min': 0}),
            'masters_degree': forms.Select(attrs={'class': 'form-select'}),
            'masters_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 85 or 8.5', 'step': '0.01', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['tenth_percentage', 'twelfth_percentage', 'graduation_degree', 'graduation_percentage']:
            self.fields[f].required = True
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

    # ── Validate against the type dropdown, return converted % (or None) ──
    def _validate_and_convert(self, value, type_choice, label):
        if value is None:
            return None
        try:
            value = Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise forms.ValidationError(f"{label}: enter a valid number.")

        if value < 0:
            raise forms.ValidationError(f"{label}: value cannot be negative.")

        if type_choice == 'CGPA':
            if value > 10:
                raise forms.ValidationError(f"{label}: CGPA cannot exceed 10.")
            return value * Decimal("9.5")
        else:  # Percentage
            if value <= 10:
                raise forms.ValidationError(
                    f"{label}: you selected Percentage but entered {value}. Did you mean CGPA?"
                )
            if value > 100:
                raise forms.ValidationError(f"{label}: percentage cannot exceed 100.")
            return value

    def clean(self):
        cleaned = super().clean()

        # Masters all-or-nothing (your existing check)
        m_deg = cleaned.get('masters_degree')
        m_pct = cleaned.get('masters_percentage')
        if m_deg and not m_pct:
            self.add_error('masters_percentage', "Enter your Masters percentage.")
        if m_pct and not m_deg:
            self.add_error('masters_degree', "Select your Masters degree.")

        # Validate + convert each qualification. add_error per field so the message
        # lands on the right input rather than as a form-wide error.
        def convert(field, type_field, label):
            try:
                return self._validate_and_convert(
                    cleaned.get(field), cleaned.get(type_field), label
                )
            except forms.ValidationError as e:
                self.add_error(field, e)
                return None

        tenth   = convert('tenth_percentage',      'tenth_type',      "10th")
        twelfth = convert('twelfth_percentage',    'twelfth_type',    "12th")
        grad    = convert('graduation_percentage', 'graduation_type', "Graduation")
        masters = convert('masters_percentage',    'masters_type',    "Masters")

        # If any conversion errored, stop here (errors already attached).
        if self.errors:
            return cleaned

        # Store the CONVERTED % back (model keeps percentages, not raw CGPA)
        cleaned['tenth_percentage']      = tenth
        cleaned['twelfth_percentage']    = twelfth
        cleaned['graduation_percentage'] = grad
        cleaned['masters_percentage']    = masters

        # Combined academic % (present values only — masters optional)
        present = [v for v in [tenth, twelfth, grad, masters] if v is not None]
        cleaned['_academic_percentage'] = (
            round(sum(present) / len(present), 2) if present else Decimal("0")
        )

        # qualify: 0 if any qualification < 60, else 1
        cleaned['_qualify'] = 0 if any(
            v is not None and v < 60 for v in [tenth, twelfth, grad, masters]
        ) else 1

        return cleaned