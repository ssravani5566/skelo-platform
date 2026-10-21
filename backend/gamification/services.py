from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from core.notifications import create_notification
from .models import XPTransaction, Badge, StudentBadge, StudentStreak

@transaction.atomic
def update_streak(student):
    today=timezone.localdate()
    streak,_=StudentStreak.objects.get_or_create(student=student)
    if streak.last_activity_date == today:
        return streak
    if streak.last_activity_date == today-timedelta(days=1): streak.current_streak += 1
    else: streak.current_streak = 1
    streak.longest_streak=max(streak.longest_streak,streak.current_streak); streak.last_activity_date=today; streak.save(update_fields=["current_streak","longest_streak","last_activity_date","updated_at"])
    return streak

@transaction.atomic
def award_xp(student, activity_type, points, description="", source_key=""):
    if points <= 0: return None
    if source_key:
        existing=XPTransaction.objects.filter(student=student,source_key=source_key).first()
        if existing: return existing
    tx=XPTransaction.objects.create(student=student,activity_type=activity_type,points=int(points),description=description,source_key=source_key)
    streak=update_streak(student)
    total=sum(XPTransaction.objects.filter(student=student).values_list("points",flat=True))
    for badge in Badge.objects.filter(is_active=True,required_xp__lte=total):
        _,created=StudentBadge.objects.get_or_create(student=student,badge=badge)
        if created: create_notification(student.user,"Badge earned",f"You earned the {badge.name} badge.","SYSTEM")
    return tx

def gamification_summary(student):
    total=sum(XPTransaction.objects.filter(student=student).values_list("points",flat=True))
    streak,_=StudentStreak.objects.get_or_create(student=student)
    badges=StudentBadge.objects.filter(student=student).select_related("badge").order_by("-awarded_at")
    return {"xp":total,"streak":{"current":streak.current_streak,"longest":streak.longest_streak,"last_activity_date":streak.last_activity_date},"badges":badges}
