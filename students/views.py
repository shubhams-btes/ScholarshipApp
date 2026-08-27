from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.sessions.models import Session
from .forms import StudentRegistrationForm
from .models import Student
from admin_panel.models import College, ExamSchedule, ExamScheduleHistory
from tests.models import Result
import random, string
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import secrets, time
from django.db import IntegrityError
import threading
import logging
logger = logging.getLogger(__name__)

def _send_otp_email(email, name, otp):
    try:
        html_message = render_to_string(
            "students/emails/otp_email.html",
            {"name": name, "otp": otp, "site_name": settings.SITE_NAME},
        )
        msg = EmailMultiAlternatives(
            subject=f"Verify Your Email – {settings.SITE_NAME} Registration",
            body=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
    except Exception:
        logger.exception("Failed to send OTP email to %s", email)


def student_register(request):
    schedule_id = request.GET.get('schedule_id')

    if not schedule_id:
        return render(request, 'tests/message.html', {
            'message': "Invalid registration link. Please use the link sent to your college."
        })

    exam_schedule = get_object_or_404(ExamSchedule, pk=schedule_id)
    college = exam_schedule.college

    # Resolve the LIVE occurrence this stable link points at.
    event = exam_schedule.current_event
    if not event or not event.is_active:
        return render(request, 'tests/message.html', {
            'message': "This exam is not currently open. Please contact the administrator."
        })

    # Registration must be open for this specific event.
    if not event.registration_enabled:
        return render(request, 'tests/message.html', {
            'message': "Registrations are currently closed for this exam. Please contact the administrator."
        })

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Duplicate guard is per-OCCURRENCE — re-registration for a NEW event is allowed.
            if Student.objects.filter(email=email, exam_schedule=event).exists():
                messages.error(request, "You are already registered for this quiz.")
                return redirect(f"{request.path}?schedule_id={schedule_id}")

            otp = ''.join(secrets.choice(string.digits) for _ in range(6))

            request.session['pending_registration'] = {
                'name': form.cleaned_data['name'],
                'email': email,
                'password': make_password(form.cleaned_data['password']),
                'stream': form.cleaned_data['stream'],
                'mobile_number': form.cleaned_data['mobile_number'],
                'exam_schedule_id': event.id           # ← bind to the live occurrence
            }
            request.session['email_otp'] = otp
            request.session['otp_expiry'] = time.time() + 600
            request.session['otp_attempts'] = 0
            request.session['otp_last_sent'] = time.time()

            threading.Thread(
                target=_send_otp_email,
                args=(email, form.cleaned_data['name'], otp),
                daemon=True,
            ).start()

            messages.info(request, f"An OTP has been sent to {email}. Please verify to complete registration.")
            return redirect('verify_email')
    else:
        form = StudentRegistrationForm()

    return render(request, 'students/student_register.html', {
        'form': form,
        'college': college,
        'exam_schedule': exam_schedule,
    })

def verify_email(request):
    if request.method == 'POST':

        otp = request.POST.get('otp')
        saved_otp = request.session.get('email_otp')
        pending_data = request.session.get('pending_registration')
        expiry = request.session.get('otp_expiry', 0)
        attempts = request.session.get('otp_attempts', 0)

        if not pending_data or not saved_otp:
            messages.error(request, "Session expired or invalid. Please register again.")
            return redirect('student_register')

        # Expiry check
        if time.time() > expiry:
            for key in ['email_otp', 'otp_expiry', 'otp_attempts', 'pending_registration']:
                request.session.pop(key, None)
            messages.error(request, "Your OTP has expired. Please register again.")
            return redirect('student_register')

        # Attempt-limit check (max 5 wrong tries)
        if attempts >= 5:
            for key in ['email_otp', 'otp_expiry', 'otp_attempts', 'pending_registration']:
                request.session.pop(key, None)
            messages.error(request, "Too many incorrect attempts. Please register again.")
            return redirect('student_register')

        if otp == saved_otp:
            exam_schedule = ExamScheduleHistory.objects.get(id=pending_data['exam_schedule_id'])
            try:
                student = Student.objects.create(
                    name=pending_data['name'],
                    email=pending_data['email'],
                    password=pending_data['password'],
                    exam_schedule=exam_schedule,
                    stream=pending_data['stream'],
                    mobile_number=pending_data['mobile_number'],
                    is_active=True
                )
            except IntegrityError:
                # Race / double-submit: already registered for this exam.
                for key in ['email_otp', 'otp_expiry', 'otp_attempts', 'pending_registration']:
                    request.session.pop(key, None)
                messages.error(request, "You are already registered for this BTES TalentQuest.")
                return redirect('student_register')

            for key in ['email_otp', 'otp_expiry', 'otp_attempts', 'pending_registration']:
                request.session.pop(key, None)

            success_message = (
                f"You have been registered successfully. Your hall ticket is {student.hall_ticket}. "
                "The login link for your BTES TalentQuest will be sent 10 minutes prior to the start."
            )
            return render(request, 'tests/message.html', {'message': success_message})

        else:
            request.session['otp_attempts'] = attempts + 1
            remaining = 5 - request.session['otp_attempts']
            messages.error(request, f"Invalid OTP. {remaining} attempt(s) remaining.")
            return redirect('verify_email')

    # GET branch (bottom of verify_email)
    expiry = request.session.get('otp_expiry')
    pending = request.session.get('pending_registration')

    # No pending registration → nothing to verify; send them back.
    if not pending or not expiry:
        messages.error(request, "Session expired. Please register again.")
        return redirect('student_register')

    resend_at = request.session.get('otp_last_sent', 0) + 60   # cooldown ends here

    return render(request, 'students/verify_email.html', {
        'otp_expiry': expiry,       # Unix seconds
        'resend_at': resend_at,     # Unix seconds — resend allowed from this moment
    })



def login_view(request):
    schedule_id = request.GET.get('schedule_id')

    if not schedule_id:
        return render(request, 'tests/message.html', {
            'message': "Invalid login link. Please use the link sent to your email."
        })

    exam_schedule = get_object_or_404(ExamSchedule, pk=schedule_id)
    college = exam_schedule.college

    # The live occurrence this stable link points at.
    event = exam_schedule.current_event
    if not event or not event.is_active:
        return render(request, 'tests/message.html', {
            'message': "This exam is not currently available. Please contact the administrator."
        })

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Resolve the student against THIS occurrence.
        student = Student.objects.filter(email=email, exam_schedule=event).first()

        if student is None or not check_password(password, student.password):
            messages.error(request, "Invalid credentials")
            return redirect(f"{request.path}?schedule_id={schedule_id}")

        # Single-session lock
        if student.current_session:
            messages.error(request, "You are already logged in from another device/browser.")
            return redirect(f"{request.path}?schedule_id={schedule_id}")

        # Already attempted?
        if Result.objects.filter(student=student, exam_schedule=event).exists():
            messages.warning(request, "You have already attempted this BTES TalentQuest.")
            return redirect(f"{request.path}?schedule_id={schedule_id}")

        # Log in
        request.session['student_id'] = student.id
        if not request.session.session_key:
            request.session.save()
        student.current_session = request.session.session_key
        student.save(update_fields=["current_session"])

        next_url = request.GET.get('next', '/quiz/start_quiz/')
        return redirect(next_url)

    return render(request, "students/login.html", {"college": college})

def resend_otp(request):

    pending = request.session.get('pending_registration')
    if not pending:
        messages.error(request, "Session expired. Please register again.")
        return redirect('student_register')

    # Rate-limit resends: at most once every 60 seconds.
    last_sent = request.session.get('otp_last_sent', 0)
    now = time.time()
    if now - last_sent < 60:
        wait = int(60 - (now - last_sent))
        messages.error(request, f"Please wait {wait}s before requesting another OTP.")
        return redirect('verify_email')

    # New OTP + fresh 10-minute window, reset attempt counter.
    otp = ''.join(secrets.choice(string.digits) for _ in range(6))
    request.session['email_otp'] = otp
    request.session['otp_expiry'] = now + 600
    request.session['otp_attempts'] = 0
    request.session['otp_last_sent'] = now

    email = pending['email']
    try:
        html_message = render_to_string(
            "students/emails/otp_email.html",
            {"name": pending['name'], "otp": otp, "site_name": settings.SITE_NAME}
        )
        msg = EmailMultiAlternatives(
            subject=f"Your new OTP – {settings.SITE_NAME} Registration",
            body=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        messages.info(request, f"A new OTP has been sent to {email}.")
    except Exception:
        messages.error(request, "Failed to resend OTP. Please try again.")

    return redirect('verify_email')


