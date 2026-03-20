from django.contrib import admin
from .models import Attendance, Department, UserProfile

admin.site.register(Department)
admin.site.register(UserProfile)
admin.site.register(Attendance)
