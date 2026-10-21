from django.urls import path
from .views import *
urlpatterns=[path("health/",HealthView.as_view()),path("",NotificationListView.as_view()),path("unread-count/",UnreadCountView.as_view()),path("<int:pk>/read/",MarkReadView.as_view()),path("mark-all-read/",MarkAllReadView.as_view())]
