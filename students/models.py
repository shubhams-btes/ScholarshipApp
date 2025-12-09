from django.db import models

from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    STREAM_CHOICES = [
        ('BTECH', 'B.Tech'),
        ('MCA', 'MCA'),
    ]

    exam_schedule = models.ForeignKey(
        'admin_panel.ExamScheduleHistory',
        on_delete=models.CASCADE,
        related_name='students',
        null=True,
        blank=True
    )

    mobile_number = models.CharField(
        max_length=10,
        validators=[
            MinLengthValidator(10),
            RegexValidator(r'^\d{10}$', "Mobile number must be exactly 10 digits.")
        ]
    )
    stream = models.CharField(max_length=10, choices=STREAM_CHOICES, default='BTECH')
    current_session = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    hall_ticket = models.CharField(max_length=20, unique=True, editable=False, blank=True)

    REQUIRED_FIELDS = ['name', 'email', 'password', 'stream', 'exam_schedule', 'mobile_number']

    def __str__(self):
        return f"{self.name} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.hall_ticket:
            prefix = "CH0125"
            start_number = 1000
            last_student = Student.objects.filter(hall_ticket__startswith=prefix).order_by('-id').first()
            if last_student and last_student.hall_ticket:
                try:
                    last_number = int(last_student.hall_ticket.replace(prefix, ''))
                except ValueError:
                    last_number = start_number
                new_number = last_number + 1
            else:
                new_number = start_number
            self.hall_ticket = f"{prefix}{new_number}"
        super().save(*args, **kwargs)
