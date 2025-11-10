# students/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.student_register, name="register"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("login/", views.login_view, name="login")
]
