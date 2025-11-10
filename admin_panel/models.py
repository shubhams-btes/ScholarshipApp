from django.db import models

# --------------------------
# 1️⃣ College - master table
# --------------------------
class College(models.Model):
    name = models.CharField(max_length=255, unique=True)  # only college name is needed

    def __str__(self):
        return self.name


# --------------------------
# 2️⃣ CollegeOfficial - multiple representatives per college
# --------------------------
class CollegeOfficial(models.Model):

    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='officials')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.college.name})"


# --------------------------
# 3️⃣ ExamSchedule - controls registration & quiz flow
# --------------------------
class ExamSchedule(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='exam_schedules')
    registration_enabled = models.BooleanField(default=True)  # can students register
    quiz_enabled = models.BooleanField(default=False)         # can students take the quiz
    quiz_date = models.DateTimeField(null=True,blank=True)       # date of quiz
    registration_link = models.URLField(blank=True)
    quiz_link = models.URLField(blank=True)
    is_active = models.BooleanField(default=False)            # only active exams are accessible

    class Meta:
        unique_together = ('college', 'quiz_date')  # optional, one exam per college per date

    def __str__(self):
        return f"{self.college.name} - {self.quiz_date or 'No date set'}"


# admin_panel/models.py

class ExamScheduleHistory(models.Model):
    college = models.ForeignKey('admin_panel.College', on_delete=models.CASCADE)
    quiz_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-quiz_date']

    def __str__(self):
        return f"{self.college.name} - {self.quiz_date.strftime('%Y-%m-%d %H:%M')}"
