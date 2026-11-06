from django.urls import path
from .views import (
    AnswerView,
    FeedbackView,
    HealthView,
    InterviewDetailView,
    InterviewFinishView,
    InterviewListView,
    InterviewTurnView,
    PracticeStartView,
    QuestionsView,
)

urlpatterns = [
    # Keep named routes before integer detail routes.
    path("practice/start/", PracticeStartView.as_view(), name="interview-practice-start"),
    path("health/", HealthView.as_view(), name="interview-health"),
    path("", InterviewListView.as_view(), name="interview-list"),
    path("<int:pk>/turn/", InterviewTurnView.as_view(), name="interview-turn"),
    path("<int:pk>/finish/", InterviewFinishView.as_view(), name="interview-finish"),
    path("<int:pk>/questions/", QuestionsView.as_view(), name="interview-questions"),
    path("<int:pk>/feedback/", FeedbackView.as_view(), name="interview-feedback"),
    path("questions/<int:pk>/answers/", AnswerView.as_view(), name="interview-answer"),
    path("<int:pk>/", InterviewDetailView.as_view(), name="interview-detail"),
]
