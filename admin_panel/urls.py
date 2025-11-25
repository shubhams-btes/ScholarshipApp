from django.urls import path
from . import views

urlpatterns = [
    # Admin login & dashboard
    path('', views.login, name='admin_login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # College Management
    path('colleges/', views.college_management, name='college_management'),
    path('colleges/add/', views.add_college, name='add_college'),
    
    # College Officials
    path('colleges/<int:college_id>/officials/add/', views.add_official, name='add_official'),
    path('officials/<int:pk>/edit/', views.edit_official, name='edit_official'),
    path('officials/<int:pk>/toggle_status/', views.toggle_college_official, name='toggle_official_status'),

    # Question Management (unchanged)
    path('questions/', views.manage_questions, name='manage_questions'),
    path('questions/add/', views.add_question, name='add_question'),
    path('questions/edit/<int:pk>/', views.edit_question, name='edit_question'),
    path('questions/upload/', views.upload_questions, name='upload_questions'),
    path('questions/toggle/<int:pk>/', views.toggle_question, name='toggle_question'),
    path('questions/toggle_all/<str:action>/', views.toggle_all_questions, name='toggle_all_questions'),


    # Quiz management (if needed)
    path('quiz/', views.exam_schedule_management, name='quiz_management'),
    path('quiz/toggle_quiz/<int:pk>/', views.toggle_quiz_status, name='toggle_quiz_status'),
    path('quiz/add/', views.add_exam_schedule, name='add_exam_schedule'),
    path('quiz/update_date/<int:pk>/', views.update_quiz_date, name='update_quiz_date'),
    path('quiz/toggle_registration/<int:pk>/', views.toggle_registration, name='toggle_registration'),
    path('quiz/share_registration/<int:schedule_id>/', views.share_registration_link, name='share_registration_link'),
    path('quiz/share_quiz/<int:schedule_id>/', views.share_quiz_link, name='share_quiz_link'),

    # College Results
    path("results/<int:schedule_id>/", views.college_results, name="college_results"),
    path('registrations/<int:schedule_id>/', views.college_registrations, name='college_registrations'),

    # Export Results

    path('export/registrations/<int:schedule_id>/', views.export_registrations, name='export_registrations'),
    path('export/results/<int:schedule_id>/', views.export_results, name='export_results'),

]
