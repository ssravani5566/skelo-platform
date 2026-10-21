from django.urls import path
from .views import *
urlpatterns=[path("health/",HealthView.as_view()),path("",SummaryView.as_view()),path("xp/",XPView.as_view()),path("badges/",BadgeListView.as_view()),path("student-badges/",StudentBadgeView.as_view()),path("streak/",StreakView.as_view())]
