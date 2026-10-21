from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include,path
urlpatterns=[
 path("admin/",admin.site.urls),path("api/auth/",include("accounts.urls")),path("api/students/",include("students.urls")),path("api/dashboard/",include("dashboard.urls")),path("api/coding/",include("coding.urls")),path("api/assessments/",include("assessments.urls")),path("api/assignments/",include("assignments.urls")),path("api/courses/",include("courses.urls")),path("api/codeathons/",include("codeathons.urls")),path("api/interviews/",include("interviews.urls")),path("api/attendance/",include("attendance.urls")),path("api/gamification/",include("gamification.urls")),path("api/notifications/",include("notifications.urls")),path("api/reports/",include("reports.urls")),path("api/search/",include("search.urls")),
]
if settings.DEBUG: urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
