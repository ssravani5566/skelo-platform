from django.urls import path
from .views import *
urlpatterns=[path("health/",HealthView.as_view()),path("",AttendanceListView.as_view()),path("summary/",AttendanceSummaryView.as_view()),path("sessions/",SessionListView.as_view()),path("sessions/<int:pk>/",SessionDetailView.as_view()),path("sessions/<int:pk>/mark/",MarkAttendanceView.as_view())]
