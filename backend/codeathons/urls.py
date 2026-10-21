from django.urls import path
from .views import *
urlpatterns=[path("health/",HealthView.as_view()),path("",CodeathonListView.as_view()),path("<int:pk>/",CodeathonDetailView.as_view()),path("<int:pk>/register/",RegisterView.as_view()),path("<int:pk>/leave/",LeaveView.as_view()),path("<int:pk>/problems/",ProblemsView.as_view()),path("<int:pk>/leaderboard/",LeaderboardView.as_view()),path("<int:pk>/submit/",SubmitView.as_view())]
