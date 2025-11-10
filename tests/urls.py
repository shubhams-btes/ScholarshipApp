from . import views
from django.urls import path

urlpatterns = [
    path('start_quiz/', views.quiz_view, name='start_quiz'),
    path("submit/", views.submit_quiz, name="submit_quiz"),
    path("submitted/", views.quiz_submitted, name="quiz_submitted"),
]
