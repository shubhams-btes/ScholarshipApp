from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    STREAM_CHOICES = [
        ('BTECH', 'B.Tech'),
        ('MCA', 'MCA'),
    ]

    # 🔹 Link to ExamSchedule instead of College
    exam_schedule = models.ForeignKey(
        'admin_panel.ExamScheduleHistory',
        on_delete=models.CASCADE,
        related_name='students',
        null=True,      # allow nulls temporarily
        blank=True
    )

    mobile_number = models.CharField(max_length=15)
    stream = models.CharField(max_length=10, choices=STREAM_CHOICES, default='BTECH')
    current_session = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['name', 'email', 'password', 'stream', 'exam_schedule', 'mobile_number']

    def __str__(self):
        return f"{self.name} ({self.email})"
