from django.urls import path
from .views import HealthView, SkillCatalogView, StudentDirectoryView, StudentProfileView, StudentSkillDetailView, StudentSkillListCreateView
urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("profile/", StudentProfileView.as_view(), name="profile"),
    path("skills/", StudentSkillListCreateView.as_view(), name="skills"),
    path("skills/<int:pk>/", StudentSkillDetailView.as_view(), name="skill-detail"),
    path("skill-catalog/", SkillCatalogView.as_view(), name="skill-catalog"),
    path("directory/", StudentDirectoryView.as_view(), name="directory"),
]
