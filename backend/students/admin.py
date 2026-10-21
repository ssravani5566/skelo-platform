from django.contrib import admin
from .models import StudentProfile, FacultyProfile, Skill, StudentSkill

admin.site.register(StudentProfile)
admin.site.register(FacultyProfile)
admin.site.register(Skill)
admin.site.register(StudentSkill)
