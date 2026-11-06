from datetime import datetime, timedelta
import csv
import os
import json
import hashlib

import requests
from django.db import transaction
from django.http import HttpResponse
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import paginated_response
from core.notifications import create_notification
from students.models import StudentProfile
from students.services import get_student_profile
from .models import AttendancePolicy, TrainingSession, Attendance, AttendanceEvent
from .serializers import AttendanceSerializer, SessionSerializer, AttendancePolicySerializer


def get_policy():
    return AttendancePolicy.objects.get_or_create(pk=1)[0]


def session_start(session):
    value = datetime.combine(session.session_date, session.start_time)
    return timezone.make_aware(value, timezone.get_current_timezone()) if timezone.is_naive(value) else value


def session_end(session):
    value = datetime.combine(session.session_date, session.end_time)
    if session.end_time <= session.start_time:
        value += timedelta(days=1)
    return timezone.make_aware(value, timezone.get_current_timezone()) if timezone.is_naive(value) else value


def student_is_eligible(session, profile):
    if session.target_department and (session.target_department.strip().casefold() != (profile.department or "").strip().casefold()):
        return False
    if session.target_year and profile.year != session.target_year:
        return False
    if session.target_semester and profile.semester != session.target_semester:
        return False
    return True


def eligible_students(session):
    students = StudentProfile.objects.select_related("user").all()
    if session.target_department:
        students = students.filter(department__iexact=session.target_department.strip())
    if session.target_year:
        students = students.filter(year=session.target_year)
    if session.target_semester:
        students = students.filter(semester=session.target_semester)
    return students


def finalize_record(record, now=None, reason="", add_final_heartbeat=True):
    """Finalize a session using capped server-observed active heartbeats, not client-supplied duration."""
    if record.status != "IN_PROGRESS":
        return record
    now = now or timezone.now()
    session = record.session
    policy = get_policy()
    if add_final_heartbeat and record.last_activity_at and not record.tracking_paused:
        delta = max(0, int((now - record.last_activity_at).total_seconds()))
        record.participation_seconds += min(delta, policy.heartbeat_credit_cap_seconds)
    attended_minutes = record.participation_seconds // 60
    required_minutes = min(
        int(session.minimum_attendance_minutes or policy.default_minimum_attendance_minutes),
        max(1, int((session_end(session) - session_start(session)).total_seconds() // 60)),
    )
    if attended_minutes < required_minutes:
        record.status = "ABSENT"
        record.remarks = reason or f"Automatic tracking recorded {attended_minutes} active minutes; {required_minutes} minutes were required."
    else:
        late_at = session_start(session) + timedelta(minutes=session.late_after_minutes)
        record.status = "LATE" if record.joined_at and record.joined_at > late_at else "PRESENT"
        record.remarks = reason or f"Automatically verified from {attended_minutes} active minutes in the session."
    record.left_at = record.left_at or now
    record.last_activity_at = now
    record.tracking_paused = False
    record.save()
    AttendanceEvent.objects.create(
        attendance=record,
        event_type="AUTO_FINALIZED",
        note=f"Final status: {record.status}; verified active time: {attended_minutes} min.",
    )
    create_notification(
        record.student.user,
        "Attendance finalized",
        f"{session.title}: {record.status.title().replace('_', ' ')}. {attended_minutes} verified active minute(s) recorded.",
        "ATTENDANCE",
    )
    return record


def process_ended_sessions(now=None):
    """Idempotently finalize expired tracked sessions and add absent records for eligible students."""
    now = now or timezone.now()
    sessions = TrainingSession.objects.filter(session_date__lte=timezone.localdate()).select_related("course")
    for session in sessions.iterator():
        if session_end(session) + timedelta(minutes=10) > now:
            continue
        records = Attendance.objects.filter(session=session).select_related("student__user", "session")
        for record in records.filter(status="IN_PROGRESS").iterator():
            finalize_record(record, now=now, reason="Session closed; attendance finalized from recorded activity.")
        # Deactivated sessions are treated as cancelled; preserve any tracked records but do not create absences.
        if not session.is_active:
            continue
        existing = set(Attendance.objects.filter(session=session).values_list("student_id", flat=True))
        missing = [student for student in eligible_students(session).iterator() if student.id not in existing]
        if missing:
            missing_ids = [student.id for student in missing]
            absent_rows = [Attendance(session=session, student=student, status="ABSENT", source="AUTOMATIC", remarks="No verified participation was recorded for this scheduled session.") for student in missing]
            Attendance.objects.bulk_create(absent_rows, ignore_conflicts=True)
            # Re-fetch inserted records because bulk_create(ignore_conflicts=True) may not populate PKs.
            for record in Attendance.objects.filter(session=session, student_id__in=missing_ids, status="ABSENT", source="AUTOMATIC").select_related("student__user"):
                if not record.events.filter(event_type="AUTO_ABSENT").exists():
                    AttendanceEvent.objects.create(attendance=record, event_type="AUTO_ABSENT", note="System finalized an ended session without verified participation.")
                    if session.session_date >= timezone.localdate() - timedelta(days=14):
                        create_notification(record.student.user, "Attendance recorded", f"{session.title}: no verified participation was recorded, so attendance is marked Absent. Request a review if this is incorrect.", "ATTENDANCE")


def _build_attendance_insight(metrics, fallback):
    """Use an optional server-side OpenAI key for a short aggregate-only summary; always retain a rule-based fallback."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return fallback, "rules"
    metrics_json = json.dumps(metrics, sort_keys=True, default=str)
    cache_key = "scott_attendance_insight_" + hashlib.sha256(metrics_json.encode("utf-8")).hexdigest()[:32]
    cached = cache.get(cache_key)
    if cached:
        return cached[0], cached[1]
    model = os.getenv("OPENAI_ATTENDANCE_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    prompt = (
        "Review these aggregate, non-identifying student attendance metrics and write 2 concise sentences for a college trainer. "
        "Describe only patterns supported by the numbers, suggest one practical supportive action, and do not infer student ability, "
        "motivation, health, or causes. Do not invent facts. Metrics: " + str(metrics)
    )
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "instructions": "You are an education operations analyst. Be careful, non-judgmental, and evidence-based.", "input": prompt, "max_output_tokens": 140},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        output_text = []
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for part in item.get("content", []):
                if part.get("type") == "output_text" and part.get("text"):
                    output_text.append(part["text"].strip())
        generated = " ".join(output_text).strip()
        if generated:
            result = (generated[:1200], "openai")
            cache.set(cache_key, result, timeout=6 * 60 * 60)
            return result
    except (requests.RequestException, ValueError, TypeError, KeyError):
        pass
    return fallback, "rules"


def _student_profile(user):
    try:
        return get_student_profile(user)
    except (StudentProfile.DoesNotExist, AttributeError):
        return None


def _require_staff(request):
    return getattr(request.user, "role", None) in ("ADMIN", "FACULTY")


class HealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok", "mode": "automatic-session-tracking"})


class AttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        process_ended_sessions()
        qs = Attendance.objects.select_related("session__trainer", "session__course", "student__user").order_by("-session__session_date", "-session__start_time")
        if request.user.role == "STUDENT":
            profile = _student_profile(request.user)
            if not profile:
                return Response({"detail": "Student profile is not available for this account."}, status=403)
            qs = qs.filter(student=profile)
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        session_id = request.query_params.get("session")
        if session_id:
            qs = qs.filter(session_id=session_id)
        return paginated_response(request, qs, AttendanceSerializer)


class AttendanceExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        process_ended_sessions()
        qs = Attendance.objects.select_related("student__user", "session__course", "session__trainer").order_by("-session__session_date", "-session__start_time")
        if request.user.role == "STUDENT":
            profile = _student_profile(request.user)
            if not profile:
                return Response({"detail": "Student profile is not available for this account."}, status=403)
            qs = qs.filter(student=profile)
        elif not _require_staff(request):
            return Response({"detail": "Staff or student access required."}, status=403)
        session_id = request.query_params.get("session")
        if session_id:
            qs = qs.filter(session_id=session_id)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="scott-attendance-report.csv"'
        writer = csv.writer(response)
        writer.writerow(["Student", "Email", "Register number", "Department", "Year", "Semester", "Session", "Date", "Type", "Course", "Status", "Verified active minutes", "Joined at", "Left at", "Source", "Remarks"])
        for record in qs.iterator():
            writer.writerow([
                record.student.user.get_full_name() or record.student.user.email,
                record.student.user.email,
                record.student.register_number,
                record.student.department,
                record.student.year or "",
                record.student.semester or "",
                record.session.title,
                record.session.session_date,
                record.session.get_session_type_display(),
                record.session.course.title if record.session.course else "",
                record.status,
                record.participation_seconds // 60,
                timezone.localtime(record.joined_at).isoformat() if record.joined_at else "",
                timezone.localtime(record.left_at).isoformat() if record.left_at else "",
                record.source,
                record.remarks,
            ])
        return response


class AttendanceSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        process_ended_sessions()
        qs = Attendance.objects.all()
        if request.user.role == "STUDENT":
            profile = _student_profile(request.user)
            if not profile:
                return Response({"detail": "Student profile is not available for this account."}, status=403)
            qs = qs.filter(student=profile)
        finalized = qs.exclude(status="IN_PROGRESS")
        total = finalized.count()
        present = finalized.filter(status__in=["PRESENT", "LATE"]).count()
        policy = get_policy()
        verified_seconds = sum(finalized.values_list("participation_seconds", flat=True))
        percentage = round(present / total * 100, 2) if total else 0
        if request.user.role == "STUDENT" and total >= 3 and percentage < float(policy.minimum_attendance_percentage):
            from notifications.models import Notification
            recent_alert = Notification.objects.filter(
                recipient=request.user,
                title="Attendance needs attention",
                created_at__gte=timezone.now() - timedelta(days=7),
            ).exists()
            if not recent_alert:
                create_notification(
                    request.user,
                    "Attendance needs attention",
                    f"Your attendance is {percentage:.1f}%, below the configured {policy.minimum_attendance_percentage}% target. Review upcoming sessions or contact your trainer if you need support.",
                    "ATTENDANCE",
                )
        return Response({
            "total_sessions": total,
            "present": finalized.filter(status="PRESENT").count(),
            "late": finalized.filter(status="LATE").count(),
            "absent": finalized.filter(status="ABSENT").count(),
            "in_progress": qs.filter(status="IN_PROGRESS").count(),
            "percentage": percentage,
            "minimum_percentage": float(policy.minimum_attendance_percentage),
            "verified_active_minutes": verified_seconds // 60,
            "needs_attention": bool(total >= 3 and (present / total * 100 if total else 0) < float(policy.minimum_attendance_percentage)),
        })


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        process_ended_sessions()
        qs = TrainingSession.objects.select_related("trainer", "course").order_by("session_date", "start_time")
        if request.user.role == "STUDENT":
            profile = _student_profile(request.user)
            if not profile:
                return Response({"detail": "Student profile is not available for this account."}, status=403)
            qs = qs.filter(
                is_active=True,
                session_date__gte=timezone.localdate(),
            ).filter(
                Q(target_department="") | Q(target_department__iexact=profile.department or "")
            ).filter(
                Q(target_year__isnull=True) | Q(target_year=profile.year)
            ).filter(
                Q(target_semester__isnull=True) | Q(target_semester=profile.semester)
            )
        elif not _require_staff(request) and request.user.role != "ADMIN":
            return Response({"detail": "This account cannot view scheduled sessions."}, status=403)
        return paginated_response(request, qs, SessionSerializer)

    def post(self, request):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        data = request.data.copy()
        policy = get_policy()
        data["trainer"] = request.data.get("trainer") or request.user.id
        data.setdefault("minimum_attendance_minutes", policy.default_minimum_attendance_minutes)
        data.setdefault("late_after_minutes", policy.default_late_after_minutes)
        data.setdefault("join_window_minutes", policy.default_join_window_minutes)
        serializer = SessionSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["end_time"] <= serializer.validated_data["start_time"]:
            return Response({"detail": "End time must be later than start time for a session on the same day."}, status=400)
        obj = serializer.save()
        return Response(SessionSerializer(obj, context={"request": request}).data, status=201)


class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        obj = get_object_or_404(TrainingSession, pk=pk)
        serializer = SessionSerializer(obj, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        start_time = serializer.validated_data.get("start_time", obj.start_time)
        end_time = serializer.validated_data.get("end_time", obj.end_time)
        if end_time <= start_time:
            return Response({"detail": "End time must be later than start time for a session on the same day."}, status=400)
        serializer.save()
        return Response(SessionSerializer(obj, context={"request": request}).data)

    def delete(self, request, pk):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        obj = get_object_or_404(TrainingSession, pk=pk)
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        return Response({"detail": "Session deactivated. Existing attendance history has been preserved."})


class SessionJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Only student accounts can join a learning session."}, status=403)
        profile = _student_profile(request.user)
        if not profile:
            return Response({"detail": "Student profile is not available for this account."}, status=403)
        session = get_object_or_404(TrainingSession.objects.select_related("course"), pk=pk, is_active=True)
        if not student_is_eligible(session, profile):
            return Response({"detail": "This session is not assigned to your department, year or semester."}, status=403)
        now = timezone.now()
        begins, ends = session_start(session), session_end(session)
        if now < begins - timedelta(minutes=session.join_window_minutes):
            return Response({"detail": f"This session opens at {timezone.localtime(begins - timedelta(minutes=session.join_window_minutes)).strftime('%I:%M %p')} ."}, status=400)
        if now > ends + timedelta(minutes=10):
            process_ended_sessions(now)
            return Response({"detail": "This session has ended. Check your attendance history for its final status."}, status=400)
        with transaction.atomic():
            record = Attendance.objects.select_for_update().filter(session=session, student=profile).first()
            if record and record.status == "IN_PROGRESS":
                record.last_activity_at = now
                record.save(update_fields=["last_activity_at", "marked_at"])
                return Response({"attendance": AttendanceSerializer(record).data, "session": SessionSerializer(session, context={"request": request}).data, "resumed": True})
            if record:
                return Response({"detail": f"Your attendance for this session is already finalized as {record.status.replace('_', ' ').title()}."}, status=409)
            record = Attendance.objects.create(
                session=session,
                student=profile,
                status="IN_PROGRESS",
                joined_at=now,
                last_activity_at=now,
                source="AUTOMATIC",
                remarks="Automatic tracking started. Keep the session active; attendance finalizes from verified participation time.",
            )
            AttendanceEvent.objects.create(attendance=record, event_type="JOINED", note="Student joined through the authenticated session room.")
        return Response({"attendance": AttendanceSerializer(record).data, "session": SessionSerializer(session, context={"request": request}).data, "resumed": False}, status=201)


class SessionHeartbeatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student account required."}, status=403)
        profile = _student_profile(request.user)
        if not profile:
            return Response({"detail": "Student profile is not available for this account."}, status=403)
        record = get_object_or_404(Attendance.objects.select_related("session"), session_id=pk, student=profile)
        if record.status != "IN_PROGRESS":
            return Response({"detail": "This attendance session is already finalized.", "attendance": AttendanceSerializer(record).data}, status=409)
        now = timezone.now()
        if now > session_end(record.session) + timedelta(minutes=10):
            record = finalize_record(record, now=now, reason="Session ended; attendance finalized automatically.")
            return Response({"attendance": AttendanceSerializer(record).data, "finalized": True})
        cap = get_policy().heartbeat_credit_cap_seconds
        if record.tracking_paused:
            # The first heartbeat after a hidden tab only re-arms tracking; it does not credit the hidden interval.
            record.tracking_paused = False
            record.last_activity_at = now
            record.save(update_fields=["tracking_paused", "last_activity_at", "marked_at"])
            AttendanceEvent.objects.create(attendance=record, event_type="RESUMED", note="Visible session page resumed; hidden time was not credited.")
            required = min(record.session.minimum_attendance_minutes, max(1, int((session_end(record.session) - session_start(record.session)).total_seconds() // 60)))
            return Response({"attendance": AttendanceSerializer(record).data, "attended_minutes": record.attended_minutes, "required_minutes": required, "remaining_minutes": max(0, required - record.attended_minutes), "finalized": False, "resumed": True})
        delta = max(0, int((now - record.last_activity_at).total_seconds())) if record.last_activity_at else 0
        record.participation_seconds += min(delta, cap)
        record.last_activity_at = now
        record.save(update_fields=["participation_seconds", "last_activity_at", "marked_at"])
        required = min(record.session.minimum_attendance_minutes, max(1, int((session_end(record.session) - session_start(record.session)).total_seconds() // 60)))
        return Response({
            "attendance": AttendanceSerializer(record).data,
            "attended_minutes": record.attended_minutes,
            "required_minutes": required,
            "remaining_minutes": max(0, required - record.attended_minutes),
            "finalized": False,
        })


class SessionPauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student account required."}, status=403)
        profile = _student_profile(request.user)
        if not profile:
            return Response({"detail": "Student profile is not available for this account."}, status=403)
        record = get_object_or_404(Attendance.objects.select_related("session"), session_id=pk, student=profile)
        if record.status != "IN_PROGRESS":
            return Response({"detail": "This attendance session is already finalized."}, status=409)
        if not record.tracking_paused:
            now = timezone.now()
            # Credit only the short, capped interval immediately before the page became hidden.
            delta = max(0, int((now - record.last_activity_at).total_seconds())) if record.last_activity_at else 0
            record.participation_seconds += min(delta, 30)
            record.tracking_paused = True
            record.last_activity_at = now
            record.save(update_fields=["participation_seconds", "tracking_paused", "last_activity_at", "marked_at"])
            AttendanceEvent.objects.create(attendance=record, event_type="PAUSED", note="Page became hidden; further participation time is paused.")
        return Response({"attendance": AttendanceSerializer(record).data, "paused": True})


class SessionLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "STUDENT":
            return Response({"detail": "Student account required."}, status=403)
        profile = _student_profile(request.user)
        if not profile:
            return Response({"detail": "Student profile is not available for this account."}, status=403)
        record = get_object_or_404(Attendance.objects.select_related("session"), session_id=pk, student=profile)
        if record.status == "IN_PROGRESS":
            now = timezone.now()
            record = finalize_record(record, now=now, reason="Student ended the session; status calculated from verified active time.")
            AttendanceEvent.objects.create(attendance=record, event_type="LEFT", note="Student ended the tracked session.")
            return Response({"attendance": AttendanceSerializer(record).data, "finalized": True})
        return Response({"attendance": AttendanceSerializer(record).data, "finalized": True})


class SessionAttendanceRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        process_ended_sessions()
        session = get_object_or_404(TrainingSession, pk=pk)
        qs = Attendance.objects.filter(session=session).select_related("student__user", "session__trainer", "session__course").order_by("student__user__last_name", "student__user__first_name", "student__user__email")
        return paginated_response(request, qs, AttendanceSerializer)


class AttendancePolicyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(AttendancePolicySerializer(get_policy()).data)

    def post(self, request):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        policy = get_policy()
        serializer = AttendancePolicySerializer(policy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "minimum_attendance_percentage" in serializer.validated_data and not (0 < float(serializer.validated_data["minimum_attendance_percentage"]) <= 100):
            return Response({"detail": "Minimum attendance percentage must be between 1 and 100."}, status=400)
        serializer.save()
        return Response(serializer.data)


class AdminAttendanceOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        process_ended_sessions()
        policy = get_policy()
        final_records = Attendance.objects.exclude(status="IN_PROGRESS")
        total = final_records.count()
        attended = final_records.filter(status__in=["PRESENT", "LATE"]).count()
        students = StudentProfile.objects.select_related("user").annotate(
            completed_sessions=Count("attendance_records", filter=~Q(attendance_records__status="IN_PROGRESS")),
            attended_sessions=Count("attendance_records", filter=Q(attendance_records__status__in=["PRESENT", "LATE"])),
        ).order_by("user__last_name", "user__first_name")
        low_attendance = []
        for student in students:
            completed = student.completed_sessions or 0
            if completed < 3:
                continue
            rate = round((student.attended_sessions or 0) / completed * 100, 1)
            if rate < float(policy.minimum_attendance_percentage):
                low_attendance.append({
                    "student_id": student.id,
                    "name": student.user.get_full_name() or student.user.email,
                    "email": student.user.email,
                    "department": student.department or "Not specified",
                    "sessions": completed,
                    "attended": student.attended_sessions or 0,
                    "percentage": rate,
                    "recommendation": "Review recent sessions and offer support; this is an attendance signal, not a judgement of ability.",
                })
        low_attendance.sort(key=lambda row: row["percentage"])
        sessions = TrainingSession.objects.select_related("trainer", "course").order_by("-session_date", "-start_time")[:8]
        fallback_insight = (
            f"{len(low_attendance)} student(s) are below the configured {policy.minimum_attendance_percentage}% attendance target. Review session-level evidence and offer supportive follow-up where appropriate."
            if low_attendance else "No students with at least three finalized sessions are currently below the configured attendance target. Continue monitoring participation trends."
        )
        insight, insight_source = _build_attendance_insight({
            "finalized_records": total,
            "overall_attendance_percentage": round(attended / total * 100, 1) if total else 0,
            "students_below_target": len(low_attendance),
            "attendance_target_percentage": float(policy.minimum_attendance_percentage),
            "active_sessions": TrainingSession.objects.filter(is_active=True).count(),
            "sessions_in_progress": Attendance.objects.filter(status="IN_PROGRESS").count(),
            "sessions_by_type": list(TrainingSession.objects.values("session_type").annotate(count=Count("id"))),
            "lowest_attendance_percentages": [row["percentage"] for row in low_attendance[:10]],
        }, fallback_insight)
        return Response({
            "sessions_total": TrainingSession.objects.filter(is_active=True).count(),
            "students_tracked": final_records.values("student_id").distinct().count(),
            "attendance_rate": round(attended / total * 100, 1) if total else 0,
            "present_today": final_records.filter(session__session_date=timezone.localdate(), status__in=["PRESENT", "LATE"]).count(),
            "in_progress": Attendance.objects.filter(status="IN_PROGRESS").count(),
            "low_attendance_count": len(low_attendance),
            "low_attendance_students": low_attendance[:20],
            "recent_sessions": SessionSerializer(sessions, many=True, context={"request": request}).data,
            "minimum_attendance_percentage": float(policy.minimum_attendance_percentage),
            "insight": insight,
            "insight_source": insight_source,
        })


class MarkAttendanceView(APIView):
    """Retained only for authorized corrections; normal attendance is automatically tracked."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not _require_staff(request):
            return Response({"detail": "Faculty or admin access required."}, status=403)
        session = get_object_or_404(TrainingSession, pk=pk)
        student = get_object_or_404(StudentProfile, pk=request.data.get("student_id"))
        status_value = request.data.get("status", "ABSENT").upper()
        if status_value not in {"PRESENT", "ABSENT", "LATE"}:
            return Response({"detail": "Correction status must be PRESENT, LATE or ABSENT."}, status=400)
        note = str(request.data.get("remarks", "")).strip()
        if not note:
            return Response({"detail": "Add a review note explaining the attendance correction."}, status=400)
        obj, _ = Attendance.objects.update_or_create(
            session=session,
            student=student,
            defaults={"status": status_value, "remarks": f"Reviewed by {request.user.email}: {note}"[:255], "source": "ADMIN_REVIEW", "left_at": timezone.now()},
        )
        AttendanceEvent.objects.create(attendance=obj, event_type="REVIEWED", note=f"{request.user.email}: {note}"[:255])
        create_notification(student.user, "Attendance correction reviewed", f"{session.title}: attendance status updated to {status_value.title()} after staff review.", "ATTENDANCE")
        return Response(AttendanceSerializer(obj).data)
