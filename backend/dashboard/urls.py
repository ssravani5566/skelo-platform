from django.urls import path
from .views import *
urlpatterns=[
    path("health/",HealthView.as_view()),
    path("admin/overview/",AdminOverviewView.as_view()),
    path("",DashboardView.as_view()),
    path("calendar/",CalendarView.as_view()),
]
