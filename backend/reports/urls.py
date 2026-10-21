from django.urls import path
from .views import *
urlpatterns=[path("health/",HealthView.as_view()),path("overview/",ReportOverviewView.as_view()),path("export.csv",ReportCSVView.as_view())]
