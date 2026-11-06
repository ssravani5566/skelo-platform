from datetime import date, timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from courses.models import Course, Lesson
from notifications.models import Notification
from students.services import get_student_profile
from gamification.services import award_xp
from .models import StudyPlan, StudyTask, StudyCheck
from .catalog import topics_for_course


def plan_data(plan):
    tasks=list(plan.tasks.select_related('lesson').order_by('scheduled_date','order','id'))
    total=len(tasks); done=sum(t.completed for t in tasks)
    return {'id':plan.id,'course':plan.course_id,'course_title':plan.course.title if plan.course_id else plan.custom_course_title,'goal':plan.goal,'start_date':plan.start_date,'end_date':plan.end_date,'hours_per_day':float(plan.hours_per_day),'status':plan.status,'progress':round(done*100/total) if total else 0,'completed_count':done,'task_count':total,'checks':[{'id':c.id,'response':c.response} for c in plan.checks.order_by('-offered_at')[:5]],'tasks':[{'id':t.id,'title':t.title,'description':t.description,'scheduled_date':t.scheduled_date,'duration_minutes':t.duration_minutes,'completed':t.completed,'lesson_id':t.lesson_id} for t in tasks]}

class StudyPlanView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=StudyPlan.objects.filter(student=request.user).select_related('course').order_by('-created_at')
        return Response({'plans':[plan_data(p) for p in qs]})
    @transaction.atomic
    def post(self,request):
        if request.user.role!='STUDENT': return Response({'detail':'Student access required.'},status=403)
        course=None
        course_id=request.data.get('course')
        course_title=str(request.data.get('course_title') or request.data.get('custom_course_title') or '').strip()[:200]
        try:
            if course_id:
                course=Course.objects.get(pk=course_id,is_published=True)
                course_title=course.title
            if not course_title:
                raise ValueError('course')
            start=date.fromisoformat(str(request.data.get('start_date')))
            days=int(request.data.get('duration_days',14)); hours=float(request.data.get('hours_per_day',1))
            if days<1 or days>180 or hours<0.5 or hours>12: raise ValueError('duration')
        except (Course.DoesNotExist,TypeError,ValueError):
            return Response({'detail':'Enter a course, valid start date, duration (1–180 days) and daily hours (0.5–12).'},status=400)
        lessons=[]
        if course:
            lessons=list(Lesson.objects.filter(module__course=course,is_published=True).select_related('module').order_by('module__order','order'))
        end=start+timedelta(days=days-1)
        StudyPlan.objects.filter(student=request.user,status='ACTIVE').update(status='PAUSED')
        plan=StudyPlan.objects.create(student=request.user,course=course,custom_course_title='' if course else course_title,goal=str(request.data.get('goal',''))[:240],start_date=start,end_date=end,hours_per_day=hours,preferred_days=request.data.get('preferred_days',[]))
        # Use the hosted syllabus when present; otherwise create a structured starter roadmap
        # from the built-in catalogue (and fall back to a reusable course-learning framework).
        minutes=max(15,int(hours*60))
        if lessons:
            items=[(lesson.title,lesson.description or lesson.module.title,lesson,lesson.duration_minutes) for lesson in lessons]
        else:
            items=[(title,description,None,minutes) for title,description in topics_for_course(course_title)]
        count=len(items)
        for idx,(title,description,lesson,duration) in enumerate(items):
            day=start+timedelta(days=min(days-1,(idx*days)//count))
            StudyTask.objects.create(plan=plan,lesson=lesson,title=title,description=description,scheduled_date=day,duration_minutes=min(minutes,max(15,duration or minutes)),order=idx+1)
        return Response(plan_data(plan),status=201)

class StudyTaskCompleteView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,pk):
        task=get_object_or_404(StudyTask,pk=pk,plan__student=request.user)
        was_completed=task.completed
        task.completed=bool(request.data.get('completed',True)); task.completed_at=timezone.now() if task.completed else None; task.save(update_fields=['completed','completed_at'])
        plan=task.plan
        if task.completed and not was_completed:
            award_xp(get_student_profile(request.user),'COURSE',10,description=f'Completed study topic: {task.title}',source_key=f'study-task-{task.id}')
        if plan.tasks.filter(completed=False).count()==0 and not was_completed:
            course_name=plan.course.title if plan.course_id else plan.custom_course_title
            plan.status='COMPLETED'; plan.save(update_fields=['status'])
            award_xp(get_student_profile(request.user),'COURSE',50,description=f'Completed study plan: {course_name}',source_key=f'study-plan-{plan.id}-complete')
            StudyCheck.objects.get_or_create(plan=plan,response='PENDING')
            Notification.objects.create(recipient=request.user,title='Study plan completed! 🎉',message=f'You completed all topics in {course_name}. Your optional knowledge check is ready in Assessments.',notification_type='ASSESSMENT')
        return Response({'task':{'id':task.id,'completed':task.completed},'plan':plan_data(plan),'test_available':plan.checks.filter(response='PENDING').exists()})

class StudyCheckView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        check=get_object_or_404(StudyCheck,pk=pk,plan__student=request.user)
        choice=request.data.get('response')
        if choice not in ('WILLING','LATER'): return Response({'detail':'Choose willing or later.'},status=400)
        check.response=choice; check.save(update_fields=['response'])
        if choice=='LATER':
            check.plan.last_reminded_at=timezone.now(); check.plan.save(update_fields=['last_reminded_at'])
            Notification.objects.create(recipient=request.user,title='Your practice test is waiting',message='No problem. Keep learning — we will remind you about your optional knowledge check.',notification_type='ASSESSMENT')
        return Response({'response':choice,'message':'Your optional practice test is ready.' if choice=='WILLING' else 'We will keep it as a reminder.'})
