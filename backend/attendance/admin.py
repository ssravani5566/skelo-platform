from django.contrib import admin
from .models import AttendancePolicy, TrainingSession, Attendance, AttendanceEvent


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "session_type", "course", "session_date", "start_time", "end_time", "is_active")
    list_filter = ("session_type", "is_active", "session_date", "target_department")
    search_fields = ("title", "description", "batch_label", "target_department")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "participation_seconds", "source", "marked_at")
    list_filter = ("status", "source", "session__session_date")
    search_fields = ("student__user__email", "student__user__first_name", "session__title")
    readonly_fields = ("joined_at", "last_activity_at", "left_at", "participation_seconds", "marked_at")


@admin.register(AttendancePolicy)
class AttendancePolicyAdmin(admin.ModelAdmin):
    list_display = ("minimum_attendance_percentage", "default_minimum_attendance_minutes", "default_late_after_minutes", "updated_at")


@admin.register(AttendanceEvent)
class AttendanceEventAdmin(admin.ModelAdmin):
    list_display = ("attendance", "event_type", "created_at")
    list_filter = ("event_type", "created_at")
    readonly_fields = ("attendance", "event_type", "note", "created_at")
