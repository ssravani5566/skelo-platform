from django.urls import path
from .views import *

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("admin/results/", AdminAssessmentResultsView.as_view()),
    path("admin/students/", AssessmentStudentsView.as_view()),
    path("", AssessmentListView.as_view()),
    path("<int:pk>/", AssessmentDetailView.as_view()),
    path("<int:pk>/start/", AssessmentStartView.as_view()),
    path("attempts/<int:pk>/", AttemptView.as_view()),
    path("attempts/<int:pk>/answer/", AttemptView.as_view()),
    path("attempts/<int:pk>/submit/", AttemptSubmitView.as_view()),
    path("attempts/<int:pk>/result/", AttemptResultView.as_view()),
    path("<int:assessment_id>/questions/", AssessmentQuestionAdminView.as_view()),
    path("<int:assessment_id>/questions/import/", AssessmentQuestionImportView.as_view()),
    path("attempts/<int:pk>/coding-answer/", AssessmentCodingAnswerView.as_view()),
]
