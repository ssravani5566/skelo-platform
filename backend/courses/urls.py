from django.urls import path
from .views import (
    HealthView, CourseListView, CourseDetailView, CourseModulesView, LessonsView,
    CourseStartView, LessonCompleteView, MyCourseProgressView, CourseEnrollView,
    MyLearningView, LessonVideoProgressView, LessonResourceView, CourseBatchesView,
    CourseBatchDetailView, CourseAdminStudentsView, CourseAssignmentsView,
    CourseModuleActivitiesView, CourseReportView, ProtectedCourseFileView,
)

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("batches/", CourseBatchesView.as_view()),
    path("batches/<int:pk>/", CourseBatchDetailView.as_view()),
    path("admin/students/", CourseAdminStudentsView.as_view()),
    path("my-learning/", MyLearningView.as_view()),
    path("progress/", MyCourseProgressView.as_view()),
    path("files/<str:kind>/<int:pk>/", ProtectedCourseFileView.as_view()),
    path("", CourseListView.as_view()),
    path("<int:pk>/", CourseDetailView.as_view()),
    path("<int:pk>/start/", CourseStartView.as_view()),
    path("<int:pk>/enroll/", CourseEnrollView.as_view()),
    path("<int:pk>/assignments/", CourseAssignmentsView.as_view()),
    path("<int:pk>/report/", CourseReportView.as_view()),
    path("<int:course_id>/modules/", CourseModulesView.as_view()),
    path("<int:course_id>/modules/<int:module_id>/activities/", CourseModuleActivitiesView.as_view()),
    path("<int:course_id>/lessons/", LessonsView.as_view()),
    path("lessons/<int:pk>/complete/", LessonCompleteView.as_view()),
    path("lessons/<int:pk>/progress/", LessonVideoProgressView.as_view()),
    path("lessons/<int:lesson_id>/resources/", LessonResourceView.as_view()),
]
