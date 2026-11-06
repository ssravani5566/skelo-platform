from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from notifications.models import Notification
from schedules.models import StudyPlan

class Command(BaseCommand):
    help='Create in-app study reminders for active plans every two days.'
    def handle(self,*args,**options):
        now=timezone.now(); cutoff=now-timedelta(days=2)
        plans=StudyPlan.objects.filter(Q(status='ACTIVE') | Q(checks__response='LATER')).filter(Q(last_reminded_at__isnull=True) | Q(last_reminded_at__lte=cutoff)).distinct()
        count=0
        for plan in plans.select_related('student','course').distinct():
            course_name = plan.course.title if plan.course_id else plan.custom_course_title
            if plan.checks.filter(response='LATER').exists() and plan.status=='COMPLETED':
                title='Your optional practice test is waiting'
                message=f'You can take the knowledge check for {course_name} whenever you feel ready. Open Schedule to continue.'
            else:
                title='Your study plan check-in 📚'
                message=f'Take a few minutes for {course_name}. Open Schedule to continue your next topic and keep your learning streak alive.'
            Notification.objects.create(recipient=plan.student,title=title,message=message,notification_type='ASSESSMENT' if plan.status=='COMPLETED' else 'COURSE')
            plan.last_reminded_at=now; plan.save(update_fields=['last_reminded_at']); count+=1
        self.stdout.write(self.style.SUCCESS(f'Created {count} study reminders.'))
