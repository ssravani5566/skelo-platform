from datetime import timedelta
from django.utils import timezone
from core.notifications import create_notification
from gamification.services import award_xp
from .models import Interview

def sync_status(interview):
    if interview.status in {"CANCELLED","COMPLETED"}: return interview
    if interview.scheduled_at and interview.scheduled_at < timezone.now():
        # Only mark completed automatically when it is already older than 2 hours; otherwise preserve scheduled status.
        if interview.scheduled_at < timezone.now()-timedelta(hours=2): interview.status="COMPLETED"; interview.save(update_fields=["status"])
    return interview

def save_feedback(interview, data):
    from .models import InterviewFeedback
    feedback,_=InterviewFeedback.objects.update_or_create(interview=interview,defaults=data)
    interview.overall_score=round((float(feedback.technical_score)+float(feedback.communication_score)+float(feedback.confidence_score))/3,2)
    interview.status="COMPLETED"; interview.save(update_fields=["overall_score","status"])
    award_xp(interview.student,"INTERVIEW",max(5,int(round(float(interview.overall_score)))),f"Interview completed: {interview.title}",source_key=f"interview:{interview.id}")
    create_notification(interview.student.user,"Interview feedback available",f"Feedback for {interview.title} is now available.","INTERVIEW")
    return feedback
