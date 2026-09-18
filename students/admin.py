from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "hall_ticket", "name", "roll_no", "email", "mobile_number")
    search_fields = ("hall_ticket", "email", "roll_no", "mobile_number")