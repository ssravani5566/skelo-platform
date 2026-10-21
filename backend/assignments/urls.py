from django.urls import path

from .views import (
    AssignmentDetailView,
    AssignmentListView,
    AssignmentSubmitView,
    HealthView,
    SubmissionDetailView,
    SubmissionListView,
)

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("", AssignmentListView.as_view()),
    path("<int:pk>/", AssignmentDetailView.as_view()),
    path("<int:pk>/submit/", AssignmentSubmitView.as_view()),
    path("submissions/", SubmissionListView.as_view()),
    path("submissions/<int:pk>/", SubmissionDetailView.as_view()),
]
