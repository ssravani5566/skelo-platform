from django.urls import path
from .views import (
    HealthView, AttendanceListView, AttendanceSummaryView, AttendanceExportView, SessionListView, SessionDetailView,
    MarkAttendanceView, SessionJoinView, SessionHeartbeatView, SessionLeaveView, SessionPauseView,
    SessionAttendanceRecordsView, AttendancePolicyView, AdminAttendanceOverviewView,
)

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("", AttendanceListView.as_view()),
    path("summary/", AttendanceSummaryView.as_view()),
    path("export/", AttendanceExportView.as_view()),
    path("policy/", AttendancePolicyView.as_view()),
    path("admin/overview/", AdminAttendanceOverviewView.as_view()),
    path("sessions/", SessionListView.as_view()),
    path("sessions/<int:pk>/", SessionDetailView.as_view()),
    path("sessions/<int:pk>/join/", SessionJoinView.as_view()),
    path("sessions/<int:pk>/heartbeat/", SessionHeartbeatView.as_view()),
    path("sessions/<int:pk>/pause/", SessionPauseView.as_view()),
    path("sessions/<int:pk>/leave/", SessionLeaveView.as_view()),
    path("sessions/<int:pk>/records/", SessionAttendanceRecordsView.as_view()),
    path("sessions/<int:pk>/mark/", MarkAttendanceView.as_view()),
]
