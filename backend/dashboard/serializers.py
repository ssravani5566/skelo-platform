from rest_framework import serializers
class DashboardSerializer(serializers.Serializer):
    student=serializers.DictField(); stats=serializers.DictField(); courses=serializers.ListField(); focus_tasks=serializers.ListField(); upcoming=serializers.ListField(); learning_chart=serializers.ListField(); notifications_unread=serializers.IntegerField()
