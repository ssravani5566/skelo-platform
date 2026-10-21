from django.urls import path
from .views import *
urlpatterns=[path("health/",HealthView.as_view()),path("",InterviewListView.as_view()),path("<int:pk>/",InterviewDetailView.as_view()),path("<int:pk>/questions/",QuestionsView.as_view()),path("questions/<int:pk>/answers/",AnswerView.as_view()),path("<int:pk>/feedback/",FeedbackView.as_view())]
