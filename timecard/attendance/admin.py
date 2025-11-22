from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ShiftLog, Schedule, LeaveRequest, Payroll

admin.site.register(ShiftLog)
admin.site.register(Schedule)
admin.site.register(LeaveRequest)
admin.site.register(Payroll)