from django.contrib import admin
from .models import XPTransaction, Badge, StudentBadge, StudentStreak

admin.site.register(XPTransaction)
admin.site.register(Badge)
admin.site.register(StudentBadge)
admin.site.register(StudentStreak)
