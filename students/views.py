from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.sessions.models import Session
from .forms import StudentRegistrationForm
from .models import Student
from admin_panel.models import College, ExamSchedule, ExamScheduleHistory
import random, string

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def student_register(request):
    college_id = request.GET.get('college_id')
    college = get_object_or_404(College, id=college_id)

    # Get latest active exam schedule
    try:
        exam_schedule = ExamSchedule.objects.filter(
            college=college,
            registration_enabled=True
        ).latest('quiz_date')
    except ExamSchedule.DoesNotExist:
        return render(request, 'tests/message.html', {
            'message': "Registrations are currently closed for this college. Please contact the administrator."
        })

    # Ensure there's a matching ExamScheduleHistory record
    exam_schedule_history, _ = ExamScheduleHistory.objects.get_or_create(
        college=exam_schedule.college,
        quiz_date=exam_schedule.quiz_date
    )

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Prevent duplicate email
            if Student.objects.filter(email=email, exam_schedule=exam_schedule_history).exists():
                messages.error(request, "You are already registered for this quiz.")
                return redirect(f"{request.path}?college_id={college_id}")

            # Create student linked to ExamScheduleHistory ✅
            student = Student.objects.create(
                name=form.cleaned_data['name'],
                email=email,
                password=make_password(form.cleaned_data['password']),
                exam_schedule=exam_schedule_history,
                stream=form.cleaned_data['stream'],
                mobile_number=form.cleaned_data['mobile_number'],
            )

            # OTP logic
            otp = generate_otp()
            request.session['email_otp'] = otp
            request.session['register_email'] = email

            send_mail(
                'Verify your email',
                f'Your OTP for registration: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False
            )

            messages.info(request, f"An OTP has been sent to {email}{otp}. Please verify to complete registration.")
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
        if otp == request.session.get('email_otp'):
            email = request.session.get('register_email')
            student = Student.objects.get(email=email)
            student.is_active = True
            student.save()
            messages.success(request, "Email verified. Registration complete!")
            request.session.pop('email_otp')
            request.session.pop('register_email')
            success_message = (
            "You have been registered successfully. "
            "You will receive the quiz link 10 minutes prior to the quiz."
            )
            return render(request, 'tests/message.html', {'message': success_message})
        else:
            messages.error(request, "Invalid OTP. Try again.")
            return redirect('verify_email')

    return render(request, 'students/verify_email.html')


def login_view(request):
    college_id = request.GET.get('college_id')
    college = None
    if college_id:
        college = get_object_or_404(College, id=college_id)

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            student = Student.objects.get(email=email)

            # 1️⃣ Check password
            if not check_password(password, student.password):
                messages.error(request, "Invalid credentials")
                return redirect(request.path + (f"?college_id={college_id}" if college_id else ""))

            # 2️⃣ Check student belongs to this college
            if college and student.exam_schedule.college.id != college.id:
                messages.error(request, "This account does not belong to the selected college.")
                return redirect(request.path + f"?college_id={college_id}")

            # ✅ Prevent multiple logins
            if student.current_session:
                messages.error(request, "You are already logged in from another device/browser.")
                return redirect(request.path + (f"?college_id={college_id}" if college_id else ""))


            # 4️⃣ Log in
            request.session['student_id'] = student.id
            # student.current_session = request.session.session_key
            # student.save()
            next_url = request.GET.get('next', '/quiz/start_quiz/')
            return redirect(next_url)

        except Student.DoesNotExist:
            print(password, email)
            messages.error(request, "Invalid credentials")
            return redirect(request.path + (f"?college_id={college_id}" if college_id else ""))

    return render(request, "students/login.html", {"college": college})


