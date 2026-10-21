from rest_framework import serializers
from .models import TrainingSession, Attendance
class SessionSerializer(serializers.ModelSerializer):
    trainer_name=serializers.SerializerMethodField()
    class Meta:
        model=TrainingSession
        fields=["id","title","description","trainer","trainer_name","session_date","start_time","end_time","location","is_active","created_at"]
        read_only_fields=["created_at"]
    def get_trainer_name(self,obj): return obj.trainer.get_full_name() if obj.trainer else "Not assigned"
class AttendanceSerializer(serializers.ModelSerializer):
    session_title=serializers.CharField(source="session.title",read_only=True)
    session_date=serializers.DateField(source="session.session_date",read_only=True)
    trainer_name=serializers.SerializerMethodField()
    class Meta:
        model=Attendance
        fields=["id","session","session_title","session_date","trainer_name","student","status","marked_at","remarks"]
    def get_trainer_name(self,obj): return obj.session.trainer.get_full_name() if obj.session.trainer else "Not assigned"
