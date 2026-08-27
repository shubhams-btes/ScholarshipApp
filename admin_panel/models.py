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


# admin_panel/models.py

# class ExamScheduleHistory(models.Model):
#     college = models.ForeignKey('admin_panel.College', on_delete=models.CASCADE)
#     quiz_date = models.DateTimeField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_active            = models.BooleanField(default=True)   # is this the live event?
#     registration_enabled = models.BooleanField(default=True)
#     quiz_enabled         = models.BooleanField(default=False)
#     class Meta:
#         ordering = ['-quiz_date']

#     def __str__(self):
#         return f"{self.college.name} - {self.quiz_date.strftime('%Y-%m-%d %H:%M')}"
    
    
# class ExamSchedule(models.Model):
#     college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='exam_schedules')
#     current_event = models.ForeignKey(ExamScheduleHistory, null=True, on_delete=models.SET_NULL, related_name='+')
#     registration_enabled = models.BooleanField(default=True)  # can students register
#     quiz_enabled = models.BooleanField(default=False)         # can students take the quiz
#     quiz_date = models.DateTimeField(null=True,blank=True)       # date of quiz
#     registration_link = models.URLField(blank=True)
#     quiz_link = models.URLField(blank=True)
#     is_active = models.BooleanField(default=False)            # only active exams are accessible

#     class Meta:
#         unique_together = ('college', 'quiz_date')  # optional, one exam per college per date

#     def __str__(self):
#         return f"{self.college.name} - {self.quiz_date or 'No date set'}"


class ExamScheduleHistory(models.Model):
    """One immutable row per event OCCURRENCE. Students/results bind here."""
    college = models.ForeignKey('admin_panel.College', on_delete=models.CASCADE, related_name='events')
    quiz_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    # authoritative, event-local state:
    is_active            = models.BooleanField(default=True)
    registration_enabled = models.BooleanField(default=True)
    quiz_enabled         = models.BooleanField(default=False)

    class Meta:
        ordering = ['-quiz_date']

    def __str__(self):
        return f"{self.college.name} - {self.quiz_date:%Y-%m-%d %H:%M}"


class ExamSchedule(models.Model):
    """One stable pointer row per college. The shared link carries THIS id."""
    college = models.OneToOneField(College, on_delete=models.CASCADE, related_name='exam_schedule')
    current_event = models.ForeignKey(
        ExamScheduleHistory, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='pointed_to_by'
    )
    registration_link = models.URLField(blank=True)
    quiz_link = models.URLField(blank=True)

    # convenience mirrors that always read the live occurrence:
    @property
    def quiz_date(self):
        return self.current_event.quiz_date if self.current_event else None

    @property
    def registration_enabled(self):
        return bool(self.current_event and self.current_event.registration_enabled)

    @property
    def quiz_enabled(self):
        return bool(self.current_event and self.current_event.quiz_enabled)

    @property
    def is_active(self):
        return bool(self.current_event and self.current_event.is_active)

    def __str__(self):
        return f"{self.college.name} - {self.quiz_date or 'No event'}"