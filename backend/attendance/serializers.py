from rest_framework import serializers
from students.models import StudentProfile
from .models import AttendancePolicy, TrainingSession, Attendance, AttendanceEvent


class SessionSerializer(serializers.ModelSerializer):
    trainer_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True, default="")
    session_type_label = serializers.CharField(source="get_session_type_display", read_only=True)
    attendance_count = serializers.SerializerMethodField()
    present_count = serializers.SerializerMethodField()
    attendance_status = serializers.SerializerMethodField()
    attended_minutes = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()

    class Meta:
        model = TrainingSession
        fields = [
            "id", "title", "description", "session_type", "session_type_label", "course", "course_title",
            "trainer", "trainer_name", "session_date", "start_time", "end_time", "location", "batch_label",
            "target_department", "target_year", "target_semester", "minimum_attendance_minutes",
            "late_after_minutes", "join_window_minutes", "is_active", "created_at", "attendance_count",
            "present_count", "attendance_status", "attended_minutes", "can_join",
        ]
        read_only_fields = ["created_at"]

    def get_trainer_name(self, obj):
        return obj.trainer.get_full_name() or obj.trainer.email if obj.trainer else "Not assigned"

    def get_attendance_count(self, obj):
        return getattr(obj, "admin_attendance_count", None) if getattr(obj, "admin_attendance_count", None) is not None else obj.attendance_records.count()

    def get_present_count(self, obj):
        value = getattr(obj, "admin_present_count", None)
        return value if value is not None else obj.attendance_records.filter(status__in=["PRESENT", "LATE"]).count()

    def _student_attendance(self, obj):
        request = self.context.get("request")
        if not request or getattr(request.user, "role", None) != "STUDENT":
            return None
        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            return None
        return Attendance.objects.filter(session=obj, student=profile).first()

    def get_attendance_status(self, obj):
        item = self._student_attendance(obj)
        return item.status if item else "NOT_JOINED"

    def get_attended_minutes(self, obj):
        item = self._student_attendance(obj)
        return item.attended_minutes if item else 0

    def get_can_join(self, obj):
        request = self.context.get("request")
        if not request or getattr(request.user, "role", None) != "STUDENT" or not obj.is_active:
            return False
        item = self._student_attendance(obj)
        return bool(not item or item.status == "IN_PROGRESS")


class AttendanceSerializer(serializers.ModelSerializer):
    session_title = serializers.CharField(source="session.title", read_only=True)
    session_date = serializers.DateField(source="session.session_date", read_only=True)
    session_type = serializers.CharField(source="session.get_session_type_display", read_only=True)
    course_title = serializers.CharField(source="session.course.title", read_only=True, default="")
    trainer_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    department = serializers.CharField(source="student.department", read_only=True, default="")
    year = serializers.IntegerField(source="student.year", read_only=True, allow_null=True)
    semester = serializers.IntegerField(source="student.semester", read_only=True, allow_null=True)
    register_number = serializers.CharField(source="student.register_number", read_only=True)
    attended_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id", "session", "session_title", "session_date", "session_type", "course_title", "trainer_name",
            "student", "student_name", "student_email", "department", "year", "semester", "register_number", "status", "marked_at", "remarks", "joined_at",
            "left_at", "attended_minutes", "participation_seconds", "source",
        ]

    def get_trainer_name(self, obj):
        return obj.session.trainer.get_full_name() or obj.session.trainer.email if obj.session.trainer else "Not assigned"

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.email


class AttendanceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceEvent
        fields = ["id", "event_type", "note", "created_at"]
        read_only_fields = fields


class AttendancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendancePolicy
        fields = [
            "minimum_attendance_percentage", "default_minimum_attendance_minutes", "default_late_after_minutes",
            "default_join_window_minutes", "heartbeat_credit_cap_seconds", "updated_at",
        ]
        read_only_fields = ["updated_at"]
