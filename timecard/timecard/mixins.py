# mixins.py
from django.contrib import messages
from attendance.utils import is_face_match


class FaceRecognitionValidationMixin:
    def validate_face(self, reference_path, uploaded_file, request):
        is_match, error = is_face_match(reference_path, uploaded_file)
        if not is_match:
            messages.error(request, error or "Face recognition failed.")
        return is_match
