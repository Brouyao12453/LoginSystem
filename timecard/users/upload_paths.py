import os
from uuid import uuid4
from django.utils.deconstruct import deconstructible
from django.core.validators import RegexValidator

@deconstructible
class PathAndRename:
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]

        # Determine a base name for the file
        if hasattr(instance, 'user') and instance.user:
            base = instance.user.username
        elif hasattr(instance, 'student_id'):
            base = instance.student_id
        elif hasattr(instance, 'title'):
            base = instance.title.replace(" ", "_")
        else:
            base = 'upload'

        filename = f"{base}_{uuid4().hex[:8]}.{ext}"
        return os.path.join(self.sub_path, filename)


student_id_format_validator = RegexValidator(
    regex=r'^\d{2}-\d{3}-\d{3} [A-Z]$',
    message="Student ID must be in the format '98-629-992 J'."
)
