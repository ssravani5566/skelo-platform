from datetime import timedelta
from django.db.models import Avg
from django.utils import timezone
from assignments.models import AssignmentSubmission
from assessments.models import StudentAssessment
from attendance.models import Attendance
from codeathons.models import CodeathonParticipant
from courses.models import CourseProgress, LessonProgress, Lesson
from gamification.models import XPTransaction, StudentStreak
from interviews.models import Interview
from students.services import get_student_profile


def report_overview(user):
    student=get_student_profile(user)
    enrolled=CourseProgress.objects.filter(student=student).count()
    total_assigned_lessons=Lesson.objects.filter(module__course__student_progress__student=student,is_published=True).count()
    completed_lessons=LessonProgress.objects.filter(student=student,completed=True).count()
    course_completion=round(completed_lessons/total_assigned_lessons*100,2) if total_assigned_lessons else 0
    accepted=student.submissions.filter(status="ACCEPTED").values("problem_id").distinct().count()
    assessments=StudentAssessment.objects.filter(student=student,status="EVALUATED")
    assessment_avg=round(float(assessments.aggregate(v=Avg("percentage"))["v"] or 0),2)
    assignment_evals=AssignmentSubmission.objects.filter(student=student,status="EVALUATED",evaluation__isnull=False)
    assignment_avg=round(float(assignment_evals.aggregate(v=Avg("evaluation__marks"))["v"] or 0),2)
    attendance_qs=Attendance.objects.filter(student=student); att_total=attendance_qs.count(); att_present=attendance_qs.filter(status__in=["PRESENT","LATE"]).count(); attendance=round(att_present/att_total*100,2) if att_total else 0
    interviews=Interview.objects.filter(student=student,status="COMPLETED"); interview_avg=round(float(interviews.aggregate(v=Avg("overall_score"))["v"] or 0),2)
    codeathons=CodeathonParticipant.objects.filter(student=student).count()
    xp=sum(XPTransaction.objects.filter(student=student).values_list("points",flat=True)); streak,_=StudentStreak.objects.get_or_create(student=student)
    readiness=round(0.30*assessment_avg + 0.25*min(accepted/20*100,100) + 0.20*course_completion + 0.10*attendance + 0.15*interview_avg,2)
    since=timezone.localdate()-timedelta(days=29); trend=[]
    for i in range(30):
        d=since+timedelta(days=i)
        trend.append({"date":d.isoformat(),"lessons":LessonProgress.objects.filter(student=student,completed=True,completed_at__date=d).count(),"accepted_problems":student.submissions.filter(status="ACCEPTED",submitted_at__date=d).values("problem_id").distinct().count(),"xp":sum(XPTransaction.objects.filter(student=student,created_at__date=d).values_list("points",flat=True))})
    return {"course_completion":course_completion,"lesson_completion":course_completion,"coding_solved":accepted,"assessment_performance":assessment_avg,"assignment_performance":assignment_avg,"attendance":attendance,"interview_performance":interview_avg,"codeathon_participation":codeathons,"xp":xp,"streak":streak.current_streak,"longest_streak":streak.longest_streak,"placement_readiness":readiness,"enrolled_courses":enrolled,"trend":trend}
