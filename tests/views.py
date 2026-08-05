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
import pytz
from datetime import timedelta,datetime
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
    
    if not guidelines_accepted:
        request.session.pop("exam_end_time", None)
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
    # Prevent multiple attempts — scoped to THIS exam schedule,
    # matching the check in submit_quiz.
    try:
        history = ExamScheduleHistory.objects.get(
            college=student.exam_schedule.college,
            quiz_date=schedule.quiz_date,
        )
        already_attempted = Result.objects.filter(
            student=student,
            exam_schedule=history,
        ).exists()
    except ExamScheduleHistory.DoesNotExist:
        # No history row yet → nobody from this college has submitted,
        # so this student can't have attempted.
        already_attempted = False

    if already_attempted:
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
            "exam_end_time": request.session.get(
                "exam_end_time",
                ""
            ),
            "schedule": schedule,
            "guidelines_accepted": guidelines_accepted
        }
    )

@student_login_required
def start_exam(request):

    EXAM_DURATION_MINUTES = 20

    # Reuse the existing end time if the exam is already in progress,
    # so a repeat call (double-click, refresh, etc.) can't reset the clock.
    end_iso = request.session.get('exam_end_time')

    if not end_iso:
        end_iso = (
            timezone.now() +
            timedelta(minutes=EXAM_DURATION_MINUTES)
        ).isoformat()

        request.session['exam_end_time'] = end_iso
        request.session['guidelines_accepted'] = True

    return JsonResponse({
        "success": True,
        "exam_end_time": end_iso,
    })

@student_login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def submit_quiz(request):
    if request.method != "POST":
        return redirect("exam")  # fallback

    student = request.student  # assuming OneToOne with User

    # -------------------------------------------------
    # 1. SERVER-SIDE DEADLINE CHECK
    # -------------------------------------------------
    GRACE_SECONDS = 15  # allow latency / auto-submit lag

    end_iso = request.session.get("exam_end_time")
    is_late = False

    if end_iso:
        try:
            exam_end_time = datetime.fromisoformat(end_iso)
        except (ValueError, TypeError):
            exam_end_time = None

        if exam_end_time is not None:
            # Guard against naive/aware mismatch
            if timezone.is_naive(exam_end_time):
                exam_end_time = timezone.make_aware(
                    exam_end_time, timezone.get_current_timezone()
                )

            deadline = exam_end_time + timedelta(seconds=GRACE_SECONDS)
            if timezone.now() > deadline:
                is_late = True
    else:
        # No end time in session → exam was never properly started,
        # or session already cleared (double submit). Treat as invalid.
        is_late = True

    # -------------------------------------------------
    # 2. GRADE ANSWERS
    # -------------------------------------------------
    score = 0
    answered_qids = []

    for key, value in request.POST.items():
        if key.startswith("q") and key != "csrfmiddlewaretoken":
            qid = key[1:]  # remove the 'q' prefix
            if not qid.isdigit():
                continue
            try:
                q = Question.objects.get(id=int(qid))
                # OPTIONAL: enforce that qid belongs to this student's exam
                # if int(qid) not in request.session.get("exam_question_ids", []):
                #     continue
                answered_qids.append(qid)
                if str(value) == str(q.correct_option):
                    score += 1
            except Question.DoesNotExist:
                continue

    # -------------------------------------------------
    # 3. RESOLVE EXAM SCHEDULE
    # -------------------------------------------------
    try:
        schedule = ExamSchedule.objects.get(
            college=student.exam_schedule.college
        )
    except ExamSchedule.DoesNotExist:
        return render(request, "tests/message.html", {
            "message": "No active exam schedule found for your college."
        })

    history, _ = ExamScheduleHistory.objects.get_or_create(
        college=student.exam_schedule.college,
        quiz_date=schedule.quiz_date,
    )

    # -------------------------------------------------
    # 4. PREVENT DOUBLE ATTEMPT
    # -------------------------------------------------
    if Result.objects.filter(student=student, exam_schedule=history).exists():
        return render(request, "tests/message.html", {
            "message": "You have already attempted the test."
        })

    # -------------------------------------------------
    # 5. RECORD RESULT (flag if late)
    # -------------------------------------------------
    if is_late:
        # POLICY CHOICE — pick one:
        #   (a) record the real score but mark it for review,
        #   (b) zero it out,
        #   (c) reject entirely (return before creating Result).
        # Below records the attempt so it can't be retried, scored 0.
        # Change to `final_score = score` if you'd rather keep it.
        final_score = 0
    else:
        final_score = score

    result = Result.objects.create(
        student=student,
        exam_schedule=history,
        quiz_date=schedule.quiz_date,
        score=final_score,
        total_questions="20",
        # is_flagged=is_late,   # add this field to your model if you want an audit trail
    )

    # -------------------------------------------------
    # 6. CLEAR SESSION / LOGOUT
    # -------------------------------------------------
    student.current_session = None
    student.save()

    auth_logout(request)
    request.session.pop("exam_question_ids", None)
    request.session.pop("guidelines_accepted", None)
    request.session.pop("exam_end_time", None)
    request.session.flush()

    return render(request, "tests/submitted.html", {
        "result": result
    })


@student_login_required
def quiz_submitted(request):
    return render(request, "tests/submitted.html")