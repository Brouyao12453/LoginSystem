from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.upload_config import UPLOAD_PATHS

# Create your models here.
gender_choices = (
    ('Male', 'Male'),
    ('Female', 'Female'),
)


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')  # <-- Add this line
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True, blank=True)
    gender = models.CharField(max_length=10, choices=gender_choices, blank=True)
    profile_image = models.ImageField(upload_to=UPLOAD_PATHS['profile_photos'], default='profile_photos/default.png')
    reference_photo = models.ImageField(upload_to=UPLOAD_PATHS['reference_photos'], null=True, blank=True)
    # Work-related Info
    employee_id = models.CharField(max_length=20, unique=True)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.username

    @classmethod
    def get_for_user(cls, user):
        """Helper method to get or create employee profile"""
        obj, created = cls.objects.get_or_create(user=user)
        if created:
            obj.first_name = user.first_name
            obj.last_name = user.last_name
            obj.employee_id = f"{user.last_name[:3].upper()}{user.first_name[:3].upper()}{obj.pk:04d}"
            obj.save()
        return obj
