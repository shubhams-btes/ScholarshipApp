# quiz/views.py
import random
from django.contrib import messages
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Question,Result
from django.utils import timezone
from students.models import Student
from admin_panel.models import ExamSchedule,ExamScheduleHistory
from functools import wraps
from django.shortcuts import redirect
from django.utils.timezone import localtime
from django.contrib.auth import logout as auth_logout
from django.views.decorators.cache import cache_control

def student_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        student_id = request.session.get('student_id')
        if not student_id:
            return redirect('/login/')  # redirect if not logged in
        # ✅ Attach the student object to the request
        request.student = get_object_or_404(Student, id=student_id)
        return view_func(request, *args, **kwargs)
    return wrapper

@student_login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def quiz_view(request):
    student = request.student
    now = timezone.now()
    try:
        schedule = ExamSchedule.objects.get(college=student.exam_schedule.college)
    except ExamSchedule.DoesNotExist:
        return render(request, 'tests/message.html', {'message': 'No active quiz schedule for your college.'})

    if not schedule.quiz_date:
        return render(request, 'tests/message.html', {'message': 'Quiz date & time not set yet.'})

    # ✅ Ensure schedule.quiz_date is aware
    quiz_datetime = schedule.quiz_date  # Convert quiz date to local time
    # Compare safely
    if now < quiz_datetime:
        return render(request, 'tests/message.html', {
            'message': f'Quiz will start at {quiz_datetime.strftime("%Y-%m-%d %H:%M")}. '
        })

    if not schedule.quiz_enabled:
        return render(request, 'tests/message.html', {'message': 'Quiz has not been enabled yet.'})

    # Prevent multiple attempts
    if Result.objects.filter(student=student).exists():
        return render(request, 'tests/message.html', {'message': 'You have already attempted the test.'})

    # Select questions
    technical = list(Question.objects.filter(category="TECH"))
    reasoning = list(Question.objects.filter(category="REAS"))
    selected_questions = random.sample(technical, min(10, len(technical))) + \
                         random.sample(reasoning, min(10, len(reasoning)))
    random.shuffle(selected_questions)

    request.session['student_id'] = student.id
    student.current_session = request.session.session_key
    student.save()

    return render(request, "tests/exam.html", {
        "student": student,
        "questions": selected_questions,
        "duration": 20,
        "schedule": schedule
    })

@student_login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def submit_quiz(request):
    if request.method == "POST":
        student = request.student  # assuming OneToOne with User
        score = 0
        answered_qids = []

        

        for key, value in request.POST.items():
            if key.startswith("q"):  # only process question fields
                qid = key[1:]  # remove the 'q' prefix
                try:
                    q = Question.objects.get(id=int(qid))
                    answered_qids.append(qid)
                    if str(value) == str(q.correct_option):
                        score += 1
                except Question.DoesNotExist:
                    continue

        # ✅ Get active exam schedule for student’s college
        try:
            schedule = ExamSchedule.objects.get(college=student.exam_schedule.college)
        except ExamSchedule.DoesNotExist:
            return render(request, "tests/message.html", {
                "message": "No active exam schedule found for your college."
            })

        

        # ✅ Store result with exam schedule history
        history, _ = ExamScheduleHistory.objects.get_or_create(
            college=student.exam_schedule.college,
            quiz_date=schedule.quiz_date
        )

        if Result.objects.filter(student=student, exam_schedule=history).exists():
            return render(request, "tests/message.html", {"message": "You have already attempted the test."})

        result = Result.objects.create(
            student=student,
            exam_schedule=history,
            quiz_date=schedule.quiz_date,
            score=score,
            total_questions='20'

        )
        
        auth_logout(request)   # from django.contrib.auth import logout as auth_logout
        request.session.flush()  # wipe the session completely

        return render(request, "tests/submitted.html", {
            "result": result
        })

    return redirect("exam")  # fallback


@student_login_required
def quiz_submitted(request):
    return render(request, "tests/submitted.html")