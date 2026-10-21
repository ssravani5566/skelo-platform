from django.db import models
from django.db.models import Q

class XPTransaction(models.Model):
    ACTIVITY_CHOICES = (("PROBLEM","Problem Solved"),("ASSESSMENT","Assessment"),("ASSIGNMENT","Assignment"),("COURSE","Course"),("INTERVIEW","Interview"),("CODEATHON","Codeathon"),("DAILY","Daily Activity"),("OTHER","Other"))
    student=models.ForeignKey("students.StudentProfile",on_delete=models.CASCADE,related_name="xp_transactions")
    activity_type=models.CharField(max_length=30,choices=ACTIVITY_CHOICES)
    points=models.IntegerField()
    description=models.CharField(max_length=255,blank=True)
    source_key=models.CharField(max_length=150,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=["student","source_key"],condition=~Q(source_key=""),name="unique_student_xp_source")]
class Badge(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True)
    icon=models.ImageField(upload_to="badges/",blank=True,null=True)
    required_xp=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name
class StudentBadge(models.Model):
    student=models.ForeignKey("students.StudentProfile",on_delete=models.CASCADE,related_name="badges")
    badge=models.ForeignKey(Badge,on_delete=models.CASCADE,related_name="students")
    awarded_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["student","badge"],name="unique_student_badge")]
class StudentStreak(models.Model):
    student=models.OneToOneField("students.StudentProfile",on_delete=models.CASCADE,related_name="streak")
    current_streak=models.PositiveIntegerField(default=0)
    longest_streak=models.PositiveIntegerField(default=0)
    last_activity_date=models.DateField(null=True,blank=True)
    updated_at=models.DateTimeField(auto_now=True)
