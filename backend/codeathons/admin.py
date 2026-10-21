from django.contrib import admin
from .models import Codeathon, CodeathonProblem, CodeathonParticipant, CodeathonSubmission

admin.site.register(Codeathon)
admin.site.register(CodeathonProblem)
admin.site.register(CodeathonParticipant)
admin.site.register(CodeathonSubmission)
