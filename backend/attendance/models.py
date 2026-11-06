from django.conf import settings
from django.db import models


class AttendancePolicy(models.Model):
    """Global defaults used by the automatic attendance engine."""
    minimum_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=75.00)
    default_minimum_attendance_minutes = models.PositiveSmallIntegerField(default=15)
    default_late_after_minutes = models.PositiveSmallIntegerField(default=10)
    default_join_window_minutes = models.PositiveSmallIntegerField(default=15)
    heartbeat_credit_cap_seconds = models.PositiveSmallIntegerField(default=75)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Attendance policy"
        verbose_name_plural = "Attendance policy"

    def __str__(self):
        return f"Attendance policy · {self.minimum_attendance_percentage}% target"


class TrainingSession(models.Model):
    SESSION_TYPES = (
        ("CLASS", "Live class"),
        ("CODING_LAB", "Coding lab"),
        ("WORKSHOP", "Workshop"),
        ("MOCK_INTERVIEW", "Mock interview"),
        ("LEARNING_LAB", "Learning session"),
        ("OTHER", "Other"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_type = models.CharField(max_length=24, choices=SESSION_TYPES, default="CLASS")
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_sessions")
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="training_sessions")
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    batch_label = models.CharField(max_length=100, blank=True, help_text="Display label only; use department/year/semester to target students.")
    target_department = models.CharField(max_length=100, blank=True)
    target_year = models.PositiveSmallIntegerField(null=True, blank=True)
    target_semester = models.PositiveSmallIntegerField(null=True, blank=True)
    minimum_attendance_minutes = models.PositiveSmallIntegerField(default=15)
    late_after_minutes = models.PositiveSmallIntegerField(default=10)
    join_window_minutes = models.PositiveSmallIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session_date", "start_time", "title"]

    def __str__(self):
        return f"{self.title} - {self.session_date}"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ("IN_PROGRESS", "In progress"),
        ("PRESENT", "Present"),
        ("LATE", "Late"),
        ("ABSENT", "Absent"),
    )
    SOURCE_CHOICES = (("AUTOMATIC", "Automatic tracking"), ("ADMIN_REVIEW", "Reviewed correction"))

    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ABSENT")
    marked_at = models.DateTimeField(auto_now=True)
    remarks = models.CharField(max_length=255, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    participation_seconds = models.PositiveIntegerField(default=0)
    tracking_paused = models.BooleanField(default=False)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="AUTOMATIC")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="unique_session_student_attendance")]
        ordering = ["-marked_at"]

    @property
    def attended_minutes(self):
        return self.participation_seconds // 60

    def __str__(self):
        return f"{self.student} - {self.session.title} - {self.status}"


class AttendanceEvent(models.Model):
    EVENT_TYPES = (
        ("JOINED", "Joined session"),
        ("PAUSED", "Tracking paused while page hidden"),
        ("RESUMED", "Tracking resumed"),
        ("LEFT", "Left session"),
        ("AUTO_FINALIZED", "Automatically finalized"),
        ("AUTO_ABSENT", "Automatically recorded absent"),
        ("REVIEWED", "Attendance correction reviewed"),
    )
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=24, choices=EVENT_TYPES)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.attendance_id} · {self.event_type}"
