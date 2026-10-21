from datetime import timedelta
from django.db.models import Count
from django.utils import timezone
from accounts.models import User
from attendance.models import Attendance
from assignments.models import Assignment, AssignmentSubmission
from assessments.models import Assessment, StudentAssessment
from codeathons.models import Codeathon, CodeathonParticipant
from courses.models import Course, CourseProgress, Lesson, LessonProgress
from gamification.models import XPTransaction, StudentStreak
from interviews.models import Interview
from notifications.models import Notification
from students.services import get_student_profile


def student_dashboard(user):
    student=get_student_profile(user); today=timezone.localdate(); since=today-timedelta(days=6)
    course_qs=Course.objects.filter(is_published=True).prefetch_related("modules__lessons")
    course_data=[]
    for c in course_qs:
        total=Lesson.objects.filter(module__course=c,is_published=True).count(); done=LessonProgress.objects.filter(student=student,lesson__module__course=c,completed=True).count(); pct=round(done/total*100,2) if total else 0
        course_data.append({"id":c.id,"title":c.title,"category":c.category,"progress":pct,"lessons":total,"completed":done,"level":c.level})
    xp=sum(XPTransaction.objects.filter(student=student).values_list("points",flat=True)); streak,_=StudentStreak.objects.get_or_create(student=student)
    solved=student.submissions.filter(status="ACCEPTED").values("problem_id").distinct().count()
    att_total=student.attendance_records.count(); att_present=student.attendance_records.filter(status__in=["PRESENT","LATE"]).count(); attendance=round(att_present/att_total*100,2) if att_total else 0
    focus=[]
    pending_assign=Assignment.objects.filter(status="PUBLISHED",due_date__gte=timezone.now()).exclude(submissions__student=student).order_by("due_date").first()
    if pending_assign: focus.append({"type":"assignment","title":pending_assign.title,"meta":f"Due {pending_assign.due_date.date().isoformat()}"})
    next_lesson=Lesson.objects.filter(is_published=True).exclude(student_progress__student=student,student_progress__completed=True).order_by("module__course_id","module__order","order").first()
    if next_lesson: focus.append({"type":"course","title":next_lesson.title,"meta":next_lesson.module.course.title})
    open_assessment=Assessment.objects.filter(is_published=True).exclude(student_attempts__student=student,student_attempts__status="EVALUATED").order_by("start_at").first()
    if open_assessment: focus.append({"type":"assessment","title":open_assessment.title,"meta":f"{open_assessment.duration_minutes} min"})
    interview=Interview.objects.filter(student=student,status="SCHEDULED",scheduled_at__gte=timezone.now()).order_by("scheduled_at").first()
    if interview: focus.append({"type":"interview","title":interview.title,"meta":interview.scheduled_at.isoformat()})
    activity_chart=[]
    for i in range(7):
        d=since+timedelta(days=i); activity_chart.append({"date":d.isoformat(),"xp":sum(XPTransaction.objects.filter(student=student,created_at__date=d).values_list("points",flat=True)),"lessons":LessonProgress.objects.filter(student=student,completed=True,completed_at__date=d).count(),"submissions":student.submissions.filter(submitted_at__date=d).count()})
    upcoming=[]
    for x in Interview.objects.filter(student=student,scheduled_at__gte=timezone.now()).order_by("scheduled_at")[:5]: upcoming.append({"type":"interview","id":x.id,"title":x.title,"at":x.scheduled_at.isoformat() if x.scheduled_at else None})
    for x in Codeathon.objects.filter(is_published=True,end_at__gte=timezone.now()).order_by("start_at")[:5]: upcoming.append({"type":"codeathon","id":x.id,"title":x.title,"at":x.start_at.isoformat()})
    for x in Assignment.objects.filter(status="PUBLISHED",due_date__gte=timezone.now()).order_by("due_date")[:5]: upcoming.append({"type":"assignment","id":x.id,"title":x.title,"at":x.due_date.isoformat()})
    upcoming=sorted(upcoming,key=lambda x:x.get("at") or "")[:6]
    return {"student":{"id":student.id,"register_number":student.register_number,"name":user.get_full_name() or user.username,"email":user.email},"stats":{"xp":xp,"streak":streak.current_streak,"longest_streak":streak.longest_streak,"problems":solved,"attendance":attendance},"courses":course_data[:8],"focus_tasks":focus[:6],"upcoming":upcoming,"learning_chart":activity_chart,"notifications_unread":Notification.objects.filter(recipient=user,is_read=False).count()}
