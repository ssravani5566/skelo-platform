from django.urls import path
from .views import StudyPlanView, StudyTaskCompleteView, StudyCheckView
urlpatterns=[path('',StudyPlanView.as_view()),path('tasks/<int:pk>/complete/',StudyTaskCompleteView.as_view()),path('checks/<int:pk>/response/',StudyCheckView.as_view())]
