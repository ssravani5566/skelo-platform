from django.urls import path
from .views import *
urlpatterns = [
    path("health/", HealthView.as_view()),
    path("", CourseListView.as_view()),
    path("progress/", MyCourseProgressView.as_view()),
    path("<int:pk>/", CourseDetailView.as_view()),
    path("<int:pk>/start/", CourseStartView.as_view()),
    path("<int:course_id>/modules/", CourseModulesView.as_view()),
    path("<int:course_id>/lessons/", LessonsView.as_view()),
    path("lessons/<int:pk>/complete/", LessonCompleteView.as_view()),
]
