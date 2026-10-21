from rest_framework import serializers
from .models import Interview
from students.models import StudentProfile
from accounts.models import User
class InterviewAdminSerializer(serializers.ModelSerializer):
    student_id=serializers.PrimaryKeyRelatedField(source="student",queryset=StudentProfile.objects.all(),write_only=True)
    interviewer=serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role__in=["ADMIN","FACULTY"]),required=False,allow_null=True)
    class Meta:
        model=Interview
        fields=["id","title","interview_type","student_id","interviewer","scheduled_at","status","role"]
