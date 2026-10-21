from django.urls import path
from .views import (
    ExternalProblemView,
    ExternalProgressView,
    ExternalSyncView,
    HealthView,
    PlatformListView,
    ProblemDetailView,
    ProblemListView,
    SubmissionDetailView,
    SubmissionListView,
)

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("platforms/", PlatformListView.as_view()),
    path("external/", ExternalProblemView.as_view()),
    path("external/sync/", ExternalSyncView.as_view()),
    path("problems/", ProblemListView.as_view()),
    path("problems/<int:pk>/", ProblemDetailView.as_view()),
    path("problems/<int:pk>/submit/", ProblemDetailView.as_view()),
    path("problems/<int:pk>/progress/", ExternalProgressView.as_view()),
    path("submissions/", SubmissionListView.as_view()),
    path("submissions/<int:pk>/", SubmissionDetailView.as_view()),
]
