from rest_framework import serializers
from .models import Badge, StudentBadge, StudentStreak
class BadgeSerializer(serializers.ModelSerializer):
    earned=serializers.SerializerMethodField(); icon_url=serializers.SerializerMethodField()
    class Meta: model=Badge; fields=["id","name","description","icon","icon_url","required_xp","is_active","earned"]
    def get_earned(self,obj):
        s=self.context.get("student"); return bool(s and StudentBadge.objects.filter(student=s,badge=obj).exists())
    def get_icon_url(self,obj):
        if not obj.icon: return None
        req=self.context.get("request"); return req.build_absolute_uri(obj.icon.url) if req else obj.icon.url
class StreakSerializer(serializers.ModelSerializer):
    class Meta: model=StudentStreak; fields=["current_streak","longest_streak","last_activity_date"]
class StudentBadgeSerializer(serializers.ModelSerializer):
    badge=BadgeSerializer(read_only=True)
    class Meta: model=StudentBadge; fields=["id","badge","awarded_at"]
from .models import XPTransaction
class XPTransactionSerializer(serializers.ModelSerializer):
    class Meta: model=XPTransaction; fields=["id","activity_type","points","description","source_key","created_at"]
