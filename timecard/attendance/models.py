
from users.upload_config import UPLOAD_PATHS
from users.models import Employee
# models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth import get_user_model
from users.upload_config import UPLOAD_PATHS
from users.models import Employee


def employee_photo_path(instance, filename):
    return f'employees/{instance.user.username}/profile/{filename}'

def shift_photo_path(instance, filename):
    return f'employees/{instance.employee.user.username}/shifts/{filename}'


User = get_user_model()


class ShiftLog(models.Model):
    """Shift log model"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_in_photo = models.ImageField(upload_to=UPLOAD_PATHS['clock_in_photo'], null=True, blank=True)

    break_start = models.DateTimeField(null=True, blank=True)
    break_start_photo = models.ImageField(upload_to=UPLOAD_PATHS['break_start_photo'], null=True, blank=True)

    break_end = models.DateTimeField(null=True, blank=True)
    break_end_photo = models.ImageField(upload_to=UPLOAD_PATHS['break_end_photo'], null=True, blank=True)

    clock_out = models.DateTimeField(null=True, blank=True)
    clock_out_photo = models.ImageField(upload_to=UPLOAD_PATHS['clock_out_photo'], null=True, blank=True)

    def is_on_break(self):
        return self.break_start and not self.break_end

    def break_elapsed(self):
        if self.break_start and not self.break_end:
            return (timezone.now() - self.break_start) >= timedelta(minutes=30)
        return False

    def __str__(self):
        return f"{self.employee.user.username} - {self.clock_in.date() if self.clock_in else 'Unstarted'}"



class Schedule(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    is_working_day = models.BooleanField(default=True)
    start_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.employee} - {self.date} ({'Working' if self.is_working_day else 'Off'})"



class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('bereavement', 'Bereavement Leave'),
        ('vacation', 'Vacation Leave'),
        ('other', 'Other Leave'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    start_date = models.DateField()
    end_date = models.DateField()
    type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    approved = models.BooleanField(default=False)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee} - {self.type} ({self.start_date} to {self.end_date})"


class Payroll(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payrolls")
    payday = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-payday']

    def __str__(self):
        return f"{self.employee} - {self.payday} (${self.amount})"
