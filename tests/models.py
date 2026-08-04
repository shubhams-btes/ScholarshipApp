from django.db import models
from students.models import Student
from admin_panel.models import ExamScheduleHistory
from django.conf import settings
class Question(models.Model):
    TECHNICAL = 'TECH'
    REASONING = 'REAS'
    CATEGORY_CHOICES = [
        (TECHNICAL, 'Technical'),
        (REASONING, 'Reasoning'),
    ]

    category = models.CharField(max_length=4, choices=CATEGORY_CHOICES)
    question_text = models.TextField()
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255, blank=True, null=True)
    option_4 = models.CharField(max_length=255, blank=True, null=True)
    correct_option = models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])
    is_active = models.BooleanField(default=True)  # new field
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_questions"
    )

    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)

    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_questions"
    )

    def __str__(self):
        return f"{self.category} - {self.question_text[:50]}"

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam_schedule = models.ForeignKey(ExamScheduleHistory, on_delete=models.SET_NULL, null=True, blank=True)
    quiz_date = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.score}/{self.total_questions}"