# quiz/views.py
import random
from urllib import request
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
import pytz
from datetime import timedelta
from django.http import JsonResponse




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
    ist = pytz.timezone('Asia/Kolkata')
    guidelines_accepted = request.session.get(
        "guidelines_accepted",
        False
    )
    try:
        schedule = ExamSchedule.objects.get(
            college=student.exam_schedule.college
        )
    except ExamSchedule.DoesNotExist:
        return render(
            request,
            'tests/message.html',
            {'message': 'No active quiz schedule for your college.'}
        )

    if not schedule.quiz_date:
        return render(
            request,
            'tests/message.html',
            {'message': 'Quiz date & time not set yet.'}
        )

    quiz_datetime = schedule.quiz_date
    quiz_datetime_ist = quiz_datetime.astimezone(ist)

    if now < quiz_datetime:
        time_diff = (quiz_datetime - now).total_seconds()

        return render(
            request,
            'tests/message.html',
            {
                'message': (
                    f'Quiz will start at '
                    f'{quiz_datetime_ist.strftime("%Y-%m-%d %H:%M")}.'
                ),
                'countdown_seconds': int(time_diff)
            }
        )

    if not schedule.quiz_enabled:
        return render(
            request,
            'tests/message.html',
            {'message': 'Quiz has not been enabled yet.'}
        )

    # Prevent multiple attempts
    if Result.objects.filter(student=student).exists():
        return render(
            request,
            'tests/message.html',
            {'message': 'You have already attempted the test.'}
        )

    EXAM_DURATION_MINUTES = 20

    # -----------------------------
    # Create timer only once
    # -----------------------------
    # if 'exam_end_time' not in request.session:
    #     request.session['exam_end_time'] = (
    #         timezone.now() +
    #         timedelta(minutes=EXAM_DURATION_MINUTES)
    #     ).isoformat()

    # exam_end_time = request.session['exam_end_time']
    exam_end_time = request.session.get(
        'exam_end_time',
        ''
    )

    # -----------------------------
    # Create question set only once
    # -----------------------------
    if 'exam_question_ids' not in request.session:

        technical = list(
            Question.objects.filter(
                category="TECH",
                is_active=True
            )
        )

        reasoning = list(
            Question.objects.filter(
                category="REAS",
                is_active=True
            )
        )

        if len(technical) < 10 or len(reasoning) < 10:
            return render(
                request,
                'tests/message.html',
                {
                    'message': (
                        'Not enough active questions available. '
                        'Contact admin.'
                    )
                }
            )

        selected_questions = (
            random.sample(technical, 10) +
            random.sample(reasoning, 10)
        )

        random.shuffle(selected_questions)

        request.session['exam_question_ids'] = [
            q.id for q in selected_questions
        ]

    # -----------------------------
    # Reload same questions
    # -----------------------------
    question_ids = request.session['exam_question_ids']

    question_map = {
        q.id: q
        for q in Question.objects.filter(id__in=question_ids)
    }

    selected_questions = [
        question_map[qid]
        for qid in question_ids
        if qid in question_map
    ]

    # Save active session
    request.session['student_id'] = student.id

    if not request.session.session_key:
        request.session.save()

    student.current_session = request.session.session_key
    student.save()

    return render(
        request,
        "tests/exam.html",
        {
            "student": student,
            "questions": selected_questions,
            "duration": EXAM_DURATION_MINUTES,
            "exam_end_time": exam_end_time,
            "schedule": schedule,
            "guidelines_accepted": guidelines_accepted
        }
    )

@student_login_required
def start_exam(request):

    EXAM_DURATION_MINUTES = 20

    request.session['exam_end_time'] = (
        timezone.now() +
        timedelta(minutes=EXAM_DURATION_MINUTES)
    ).isoformat()

    request.session['guidelines_accepted'] = True

    return JsonResponse({
        "success": True
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
        
        # ✅ Clear session info (logout)
        student.current_session = None
        student.save()

        auth_logout(request)   # from django.contrib.auth import logout as auth_logout
        request.session.pop('exam_question_ids', None)
        request.session.pop('guidelines_accepted', None)
        request.session.pop('exam_end_time', None)
        request.session.flush()  # wipe the session completely

        return render(request, "tests/submitted.html", {
            "result": result
        })

    return redirect("exam")  # fallback


@student_login_required
def quiz_submitted(request):
    return render(request, "tests/submitted.html")