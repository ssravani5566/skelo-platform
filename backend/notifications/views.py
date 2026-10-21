from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.api import paginated_response
from .models import Notification
from .serializers import NotificationSerializer
class HealthView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"status":"ok"})
class NotificationListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=Notification.objects.filter(recipient=request.user).order_by("-created_at")
        unread=request.query_params.get("unread")
        if unread in {"true","false"}: qs=qs.filter(is_read=unread=="true")
        return paginated_response(request,qs,NotificationSerializer)
class UnreadCountView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response({"count":Notification.objects.filter(recipient=request.user,is_read=False).count()})
class MarkReadView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,pk):
        obj=get_object_or_404(Notification,pk=pk,recipient=request.user); obj.is_read=True; obj.read_at=timezone.now(); obj.save(update_fields=["is_read","read_at"]); return Response(NotificationSerializer(obj).data)
class MarkAllReadView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        now=timezone.now(); Notification.objects.filter(recipient=request.user,is_read=False).update(is_read=True,read_at=now); return Response({"detail":"All notifications marked as read."})
