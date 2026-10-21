from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def ensure_student_profile(sender, instance, created, **kwargs):
    if instance.role != User.ROLE_STUDENT:
        return
    from students.services import create_student_profile
    create_student_profile(instance)
