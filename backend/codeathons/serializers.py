from django.utils import timezone
from rest_framework import serializers
from .models import Codeathon, CodeathonParticipant, CodeathonProblem
from coding.serializers import ProblemListSerializer

class CodeathonSerializer(serializers.ModelSerializer):
    status=serializers.SerializerMethodField(); participants=serializers.SerializerMethodField(); registered=serializers.SerializerMethodField()
    class Meta:
        model=Codeathon
        fields=["id","title","description","event_type","category","difficulty","participation_type","mode","registration_opens_at","registration_closes_at","venue","instructions","prizes","start_at","end_at","max_participants","is_published","created_by","created_at","status","participants","registered"]
        read_only_fields=["created_by","created_at","status","participants","registered"]
    def get_status(self,obj):
        now=timezone.now()
        if not obj.is_published: return "Draft"
        if now < obj.start_at:
            if obj.registration_opens_at and now < obj.registration_opens_at: return "Registration Upcoming"
            if obj.registration_closes_at and now > obj.registration_closes_at: return "Registration Closed"
            return "Open" if (not obj.registration_opens_at or now >= obj.registration_opens_at) else "Upcoming"
        if obj.start_at <= now <= obj.end_at: return "Live"
        return "Completed"
    def get_participants(self,obj): return obj.participants.count()
    def get_registered(self,obj):
        student=self.context.get("student")
        return bool(student and obj.participants.filter(student=student).exists())
class CodeathonProblemSerializer(serializers.ModelSerializer):
    problem=serializers.SerializerMethodField()
    class Meta:
        model=CodeathonProblem
        fields=["id","problem","order","points"]
    def get_problem(self,obj): return ProblemListSerializer(obj.problem,context={"student":self.context.get("student")}).data
class ParticipantSerializer(serializers.ModelSerializer):
    student_name=serializers.CharField(source="student.user.get_full_name",read_only=True)
    class Meta:
        model=CodeathonParticipant
        fields=["id","student","student_name","registered_at","score","rank"]
