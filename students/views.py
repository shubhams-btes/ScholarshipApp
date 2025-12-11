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

            # Prevent duplicate registration for same exam
            if Student.objects.filter(email=email, exam_schedule=exam_schedule_history).exists():
                messages.error(request, "You are already registered for this quiz.")
                return redirect(f"{request.path}?college_id={college_id}")

            # ✅ Save form data in session (not DB)
            request.session['pending_registration'] = {
                'name': form.cleaned_data['name'],
                'email': email,
                'password': make_password(form.cleaned_data['password']),
                'stream': form.cleaned_data['stream'],
                'mobile_number': form.cleaned_data['mobile_number'],
                'exam_schedule_id': exam_schedule_history.id
            }

            # ✅ Generate and send OTP
            otp = generate_otp()
            request.session['email_otp'] = otp

            
            try:
                send_mail(
                    subject="Verify Your Email – Scholarship Test Registration",
                    message=(
                        "Dear Student,\n\n"
                        "Thank you for registering for the Scholarship Test.\n\n"
                        f"Your One-Time Password (OTP) for email verification is:\n\n"
                        f"OTP: {otp}\n\n"
                        "Please enter this OTP on the registration page to complete your verification.\n\n"
                        "If you did not initiate this request, please ignore this email.\n\n"
                        "Warm regards,\n"
                        "BTES Examination Support\n"
                        "Email: support@btes.org\n"
                        "Phone: +91-XXXXXXXXXX\n"
                        "Address: BTES, Bangalore, India"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )

                messages.info(request, f"An OTP has been sent to {email}. Please verify to complete registration.")
            except Exception as e:
                messages.error(request, f"❌ Failed to send OTP to {email}. Please try again later.")

            
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

        if not pending_data:
            messages.error(request, "Session expired or invalid. Please register again.")
            return redirect('student_register')

        if otp == saved_otp:
            # ✅ Create the student only after OTP verification
            exam_schedule = ExamScheduleHistory.objects.get(id=pending_data['exam_schedule_id'])

            student = Student.objects.create(
                name=pending_data['name'],
                email=pending_data['email'],
                password=pending_data['password'],
                exam_schedule=exam_schedule,
                stream=pending_data['stream'],
                mobile_number=pending_data['mobile_number'],
                is_active=True
            )

            # Cleanup session data
            for key in ['email_otp', 'pending_registration']:
                request.session.pop(key, None)

            messages.success(request, "Email verified. Registration complete!")
            success_message = (
                f"You have been registered successfully. Your hall ticket is {student.hall_ticket}. "
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

            # 3️⃣ Check if student already attempted the quiz
            already_attempted = Result.objects.filter(
                student_id=student.id,
                exam_schedule_id=student.exam_schedule.id
            ).exists()

            if already_attempted:
                messages.warning(request, "You have already attempted this quiz.")
                return redirect(request.path + (f"?college_id={college_id}" if college_id else ""))

            # 4️⃣ Log in
            request.session['student_id'] = student.id
            student.current_session = request.session.session_key
            student.save()
            next_url = request.GET.get('next', '/quiz/start_quiz/')
            return redirect(next_url)

        except Student.DoesNotExist:
            print(password, email)
            messages.error(request, "Invalid credentials")
            return redirect(request.path + (f"?college_id={college_id}" if college_id else ""))

    return render(request, "students/login.html", {"college": college})


