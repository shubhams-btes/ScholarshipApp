from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.forms import modelformset_factory
from .forms import QuestionForm, CollegeForm, ExamScheduleForm, CollegeOfficialForm,CollegeOfficialEditForm
from tests.models import Result, Question
from admin_panel.models import College, CollegeOfficial, ExamSchedule, ExamScheduleHistory
from students.models import Student
import datetime
from django.utils.timezone import make_aware, get_default_timezone
from django.contrib.auth import logout as auth_logout
import json
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font
from django.views.decorators.cache import never_cache
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime

# -----------------------------
# Decorators
# -----------------------------
def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

# -----------------------------
# Login
# -----------------------------
def login(request):
    from django.contrib.auth import authenticate, login as auth_login
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials or not a superuser.")
    return render(request, 'admin_panel/login.html')


def logout(request):
    """
    Logs out the current user and redirects to the admin login page.
    """
    auth_logout(request)
    return redirect('admin_login')  # Replace 'admin_login' with your login view URL name

# -----------------------------
# Dashboard
# -----------------------------
@never_cache
@superuser_required
def dashboard(request):
    college_query = request.GET.get('college')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    schedules = ExamScheduleHistory.objects.all()

    if college_query:
        schedules = schedules.filter(college__name__icontains=college_query)

    if from_date_str:
        from_date = parse_date(from_date_str)
        if from_date:
            from_dt = timezone.make_aware(datetime.combine(from_date, datetime.min.time()))
            schedules = schedules.filter(quiz_date__gte=from_dt)

    if to_date_str:
        to_date = parse_date(to_date_str)
        if to_date:
            to_dt = timezone.make_aware(datetime.combine(to_date, datetime.max.time()))
            schedules = schedules.filter(quiz_date__lte=to_dt)

    schedules = schedules.select_related('college').order_by('-quiz_date')

    return render(request, 'admin_panel/dashboard.html', {
        'schedules': schedules,
        'college_query': college_query,
        'from_date': from_date_str,
        'to_date': to_date_str,
    })


# -----------------------------
# College Management
# -----------------------------
@superuser_required
def college_management(request):
    # Fetch all colleges
    colleges = College.objects.all().order_by('name')
    
    # Prepare a flattened list: each official gets a row, or a placeholder if none
    officials_list = []
    for college in colleges:
        college_officials = college.officials.all().order_by('name')
        if college_officials.exists():
            for official in college_officials:
                officials_list.append(official)
        else:
            # Create a dummy object with empty fields for display
            class DummyOfficial:
                def __init__(self, college):
                    self.college = college
                    self.name = None
                    self.email = None
                    self.is_active = None
                    self.id = None  # so template won't break

            officials_list.append(DummyOfficial(college))
    
    return render(request, 'admin_panel/college_management.html', {'officials': officials_list})



@superuser_required
def add_college(request):
    if request.method == "POST":
        form = CollegeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "College added successfully.")
            return redirect('college_management')
    else:
        form = CollegeForm()
    return render(request, "admin_panel/add_edit_college.html", {"form": form, "title": "Add College"})

@superuser_required
def add_official(request, college_id=None):
    if college_id:
        college = get_object_or_404(College, pk=college_id)
    else:
        college = None

    if request.method == "POST":
        form = CollegeOfficialForm(request.POST)
        if form.is_valid():
            official = form.save(commit=False)
            if college:
                official.college = college
                official.is_active = True  # New officials are active by default
            official.save()
            messages.success(request, "Official added successfully.")
            return redirect("college_management")
    else:
        form = CollegeOfficialForm(initial={"college": college} if college else None)

    return render(request, "admin_panel/add_edit_official.html", {"form": form, "title": "Add College Official"})

@superuser_required
def edit_official(request, pk):
    official = get_object_or_404(CollegeOfficial, pk=pk)
    if request.method == 'POST':
        form = CollegeOfficialEditForm(request.POST, instance=official)
        if form.is_valid():
            form.save()
            messages.success(request, "Official updated successfully.")
            return redirect('college_management')
    else:
        form = CollegeOfficialEditForm(instance=official)

    return render(request, 'admin_panel/add_edit_official.html', {
        'form': form,
        'title': f'Edit Official: {official.name}'
    })


@superuser_required
def toggle_college_official(request, pk):
    official = get_object_or_404(CollegeOfficial, pk=pk)
    official.is_active = not official.is_active
    official.save()
    status = "activated" if official.is_active else "deactivated"
    messages.success(request, f"{official.name} ({official.college.name}) has been {status}.")
    return redirect('college_management')


# -----------------------------
# Exam Schedule Management
# -----------------------------
@superuser_required
def exam_schedule_management(request):
    colleges = College.objects.prefetch_related('exam_schedules').order_by('name')
    # Prepare rows: one per college per schedule, or dummy if no schedule
    rows = []
    for college in colleges:
        schedules = college.exam_schedules.all().order_by('quiz_date')
        if schedules.exists():
            for schedule in schedules:
                rows.append({
                    "college": college,
                    "schedule": schedule
                })
        else:
            rows.append({
                "college": college,
                "schedule": None
            })

    return render(request, 'admin_panel/quiz_management.html', {"rows": rows,"now":timezone.localtime(timezone.now())})

@superuser_required
def add_exam_schedule(request):
    college_id = request.POST.get('college') or request.GET.get('college_id')
    college = get_object_or_404(College, pk=college_id)

    if request.method == 'POST':
        quiz_date_str = request.POST.get('quiz_date')
        if not quiz_date_str:
            messages.error(request, "Quiz date is required.")
            return redirect('quiz_management')

        try:
            # Convert string from datetime-local input to naive datetime
            # Example format from datetime-local: '2025-08-27T17:15'
            naive_dt = datetime.datetime.strptime(quiz_date_str, "%Y-%m-%dT%H:%M")
            
            # Make it timezone-aware in your local timezone (Asia/Kolkata)
            aware_dt = make_aware(naive_dt, get_default_timezone())
            if aware_dt < timezone.now():
                messages.error(request, "You cannot select a past date for the quiz.")
                return redirect('quiz_management')
        except Exception as e:
            messages.error(request, f"Invalid date/time format: {e}")
            return redirect('quiz_management')

        # Check if a schedule already exists for this college
        schedule, created = ExamSchedule.objects.get_or_create(
            college=college,
            defaults={
                'quiz_date': aware_dt,
                'registration_enabled': True,
                'quiz_enabled': False,
                'is_active': False
            }
        )

        if not created:
            # Update the existing schedule
            schedule.quiz_date = aware_dt
            schedule.registration_enabled = True
            schedule.quiz_enabled = False
            schedule.is_active = False
            schedule.save(update_fields=['quiz_date', 'registration_enabled', 'quiz_enabled', 'is_active'])
            messages.success(request, f"Exam schedule updated for {college.name}.")
        else:
            messages.success(request, f"Exam schedule created for {college.name}.")
         # ✅ always log in history
        
        ExamScheduleHistory.objects.create(college=college, quiz_date=aware_dt)

        return redirect('quiz_management')

    # If GET, just show inline datepicker (handled in your template)
    messages.error(request, "Invalid request method.")
    return redirect('quiz_management')




@superuser_required
def edit_exam_schedule(request, pk):
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    if request.method == 'POST':
        form = ExamScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam schedule updated successfully.")
            return redirect('quiz_management')
    else:
        form = ExamScheduleForm(instance=schedule)
    return render(request, 'admin_panel/add_edit_exam_schedule.html', {'form': form, 'title': 'Edit Exam Schedule'})


@superuser_required
def toggle_quiz_status(request, pk):
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    
    if schedule.quiz_enabled:
        # Currently enabled → disable and clear date
        schedule.quiz_enabled = False
        schedule.quiz_date = None
        schedule.registration_enabled = False
    else:
        # Currently disabled → enable (keep date empty for now, user can set)
        schedule.quiz_enabled = True
        
    schedule.save(update_fields=['quiz_enabled', 'quiz_date','registration_enabled'])
    
    status = "enabled" if schedule.quiz_enabled else "disabled"
    messages.success(request, f"Quiz {status} for {schedule.college.name}.")
    return redirect('quiz_management')



# -----------------------------
# Quiz Management (optional simplified)
# -----------------------------
@superuser_required
def share_registration_link(request, schedule_id):
    schedule = get_object_or_404(ExamSchedule, pk=schedule_id)
    # link = f"{settings.SITE_URL}/student/register/?college_id={schedule.college.id}"
    link = f"127.0.0.1:8000/register/?college_id={schedule.college.id}"
    schedule.registration_link = link
    schedule.save(update_fields=['registration_link'])
    # Send to all active college officials
    emails = schedule.college.officials.filter(is_active=True).values_list('email', flat=True)
    send_mail(
        'College Registration Link',
        f'Your registration link: {link}',
        settings.DEFAULT_FROM_EMAIL,
        list(emails),
        fail_silently=False
    )
    messages.success(request, f"Registration link sent to {schedule.college.name} officials.")
    return redirect('quiz_management')


@superuser_required
def share_quiz_link(request, schedule_id):
    schedule = get_object_or_404(ExamSchedule, pk=schedule_id)
    schedule_history, _ = ExamScheduleHistory.objects.get_or_create(
        college=schedule.college,
        quiz_date=schedule.quiz_date,
    )
    # link = f"{settings.SITE_URL}/student/quiz/?college_id={schedule.college.id}"
    link = f"127.0.0.1:8000/login/?college_id={schedule.college.id}"
    schedule.quiz_link = link
    schedule.save(update_fields=['quiz_link'])
    # Send to all registered officials (you can filter further if needed)
    students = Student.objects.filter(exam_schedule=schedule_history)
    emails = students.values_list('email', flat=True)
    # if emails:
    #     send_mail(
    #         subject="Quiz Link",
    #         message=(
    #             f"Dear Student,\n\n"
    #             f"You have been registered for the quiz scheduled on {schedule.quiz_date}.\n"
    #             f"Here is your quiz link: {link}\n\n"
    #             f"You will be able to access the quiz 10 minutes before the start time.\n\n"
    #             f"Best of luck!"
    #         ),
    #         from_email=settings.DEFAULT_FROM_EMAIL,
    #         recipient_list=list(emails),
    #         fail_silently=False
    #     )
    send_mail(
            'College Registration Link',
            f'Your registration link: {link}',
            settings.DEFAULT_FROM_EMAIL,
            list(emails),
            fail_silently=False
    )
    messages.success(request, f"Quiz link sent for {schedule.college.name}.")
    return redirect('quiz_management')


@superuser_required
def update_quiz_date(request, pk):
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    if request.method == 'POST':
        quiz_date = request.POST.get('quiz_date')
        if quiz_date:
            schedule.quiz_date = quiz_date
            schedule.save(update_fields=['quiz_date'])
            messages.success(request, f"Quiz date updated for {schedule.college.name}.")
    return redirect('quiz_management')


@superuser_required
def toggle_registration(request, pk):
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    schedule.registration_enabled = not schedule.registration_enabled
    schedule.save(update_fields=['registration_enabled'])
    status = "opened" if schedule.registration_enabled else "closed"
    messages.success(request, f"Registration {status} for {schedule.college.name}.")
    return redirect('quiz_management')


# -----------------------------
# Results per College
# -----------------------------
@superuser_required
def college_results(request, schedule_id):
    schedule = get_object_or_404(ExamScheduleHistory, pk=schedule_id)
    college = schedule.college

    # Get results only for this exam schedule
    results = Result.objects.filter(exam_schedule=schedule).order_by("-score")

    # Apply optional filters
    cutoff = request.GET.get("cutoff")
    top_n = request.GET.get("top_n")

    filtered_results = results
    if cutoff:
        filtered_results = filtered_results.filter(score__gte=int(cutoff))
    if top_n:
        filtered_results = filtered_results[:int(top_n)]

    return render(request, "admin_panel/results.html", {
        "college": college,
        "schedule": schedule,
        "college_results": results,
        "filtered_results": filtered_results,
    })


@superuser_required
def college_registrations(request, schedule_id):
    # Get the quiz schedule
    schedule = get_object_or_404(ExamScheduleHistory, pk=schedule_id)
    college = schedule.college

    # Fetch all students registered for this quiz schedule
    registered_students = Student.objects.filter(exam_schedule=schedule).order_by('name')

    return render(request, "admin_panel/registrations.html", {
        "college": college,
        "schedule": schedule,
        "registered_students": registered_students
    })

# -----------------------------
# Question Management
# -----------------------------
@superuser_required
def manage_questions(request):
    questions = Question.objects.all().order_by('-id')
    paginator = Paginator(questions, 10)  # paginate by 10
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'admin_panel/manage_questions.html', {'page_obj': page_obj})


@superuser_required
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Question added successfully.")
            return redirect('manage_questions')
    else:
        form = QuestionForm()
    return render(request, 'admin_panel/add_edit_question.html', {'form': form, 'title': 'Add Question'})


@superuser_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully.")
            return redirect('manage_questions')
    else:
        form = QuestionForm(instance=question)
    return render(request, 'admin_panel/add_edit_question.html', {'form': form, 'title': 'Edit Question'})




@superuser_required
@require_http_methods(["GET", "POST"])
def upload_questions(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, "Please select a file to upload.")
            return redirect('upload_questions')

        # Only allow JSON or text files
        if not (file.name.endswith('.json') or file.name.endswith('.txt')):
            messages.error(request, "Only .json or .txt files are supported.")
            return redirect('upload_questions')

        try:
            # Read file content
            data = file.read().decode('utf-8')

            # Try to parse JSON directly
            questions_data = json.loads(data)

            if not isinstance(questions_data, list):
                messages.error(request, "Invalid JSON format. Expected a list of questions.")
                return redirect('upload_questions')

            count = 0
            for q in questions_data:
                # Safely extract fields
                category = q.get("category", "").strip()
                question_text = q.get("question_text", "").strip()
                option_1 = q.get("option_1", "").strip()
                option_2 = q.get("option_2", "").strip()
                option_3 = q.get("option_3", "").strip()
                option_4 = q.get("option_4", "").strip()
                correct_option = q.get("correct_option", None)

                if not question_text or correct_option not in [1, 2, 3, 4]:
                    continue  # skip invalid question

                # Save question
                Question.objects.create(
                    category=category,
                    question_text=question_text,
                    option_1=option_1,
                    option_2=option_2,
                    option_3=option_3,
                    option_4=option_4,
                    correct_option=correct_option
                )
                count += 1

            messages.success(request, f"{count} questions uploaded successfully!")
            return redirect('manage_questions')

        except json.JSONDecodeError:
            messages.error(request, "Invalid JSON format. Please check your file.")
        except Exception as e:
            messages.error(request, f"Error while processing file: {str(e)}")

        return redirect('upload_questions')

    # GET method — render upload page
    return render(request, 'admin_panel/upload_questions.html')



# Export Routes

@superuser_required
def export_registrations(request, schedule_id):
    schedule = get_object_or_404(ExamScheduleHistory, pk=schedule_id)
    students = Student.objects.filter(exam_schedule=schedule).order_by('name')

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Registrations_{schedule.college.name}"

    # Header row
    headers = ["ID", "Name", "Email", "College", "Contact Number"]
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_index, value=header.upper())
        cell.font = Font(bold=True)

    # Data rows
    for idx, student in enumerate(students, start=1):
        row = [
            idx,
            student.name.upper() if student.name else "",
            student.email.upper() if student.email else "",
            student.exam_schedule.college.name.upper() if student.exam_schedule.college.name else "",
            student.mobile_number.upper() if student.mobile_number else ""
        ]
        for col_index, value in enumerate(row, start=1):
            ws.cell(row=idx+1, column=col_index, value=value)

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Registrations_{schedule.college.name}_{schedule.quiz_date.date()}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@superuser_required
def export_results(request, schedule_id):
    schedule = get_object_or_404(ExamScheduleHistory, pk=schedule_id)
    results = Result.objects.filter(exam_schedule=schedule).order_by('-score')

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Results_{schedule.college.name}"

    # Header row
    headers = ["ID", "Student Name", "Email", "Score","College", "Contact Number"]
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_index, value=header.upper())
        cell.font = Font(bold=True)

    # Data rows
    for idx, result in enumerate(results, start=1):
        row = [
            idx,
            result.student.name.upper() if result.student.name else "",
            result.student.email.upper() if result.student.email else "",
            result.score,
            result.exam_schedule.college.name.upper() if result.exam_schedule.college.name else "",
            result.student.mobile_number.upper() if result.student.mobile_number else ""
        ]
        for col_index, value in enumerate(row, start=1):
            ws.cell(row=idx+1, column=col_index, value=value)

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Results_{schedule.college.name}_{schedule.quiz_date.date()}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
