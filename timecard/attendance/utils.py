
"""import face_recognition

def is_face_match(reference_path, uploaded_file):
    print(' from is_face match :reference_path and uploaded_file', reference_path, uploaded_file)
    try:
        # Load reference image
        reference_image = face_recognition.load_image_file(reference_path)
        reference_encodings = face_recognition.face_encodings(reference_image)
        if not reference_encodings:
            return False, "No face found in reference image"
        reference_encoding = reference_encodings[0]

        # Load uploaded image
        uploaded_image = face_recognition.load_image_file(uploaded_file)
        uploaded_encodings = face_recognition.face_encodings(uploaded_image)
        if not uploaded_encodings:
            return False, "No face found in uploaded photo"
        uploaded_encoding = uploaded_encodings[0]

        # Compare faces
        results = face_recognition.compare_faces([reference_encoding], uploaded_encoding)
        return results[0], None if results[0] else "Faces do not match"
    except Exception as e:
        print("Face match error:", e)
        return False, str(e)"""

import face_recognition
from users.models import Employee

def is_ajax(request):
    """Check if the request is an AJAX request"""
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def is_face_match(reference_path, uploaded_file):
    #Check if an uploaded photo matches the reference photo
    try:
        reference_image = face_recognition.load_image_file(reference_path)
        reference_encodings = face_recognition.face_encodings(reference_image)
        if not reference_encodings:
            return False, "No face found in reference image."

        uploaded_image = face_recognition.load_image_file(uploaded_file)
        uploaded_encodings = face_recognition.face_encodings(uploaded_image)
        if not uploaded_encodings:
            return False, "No face found in uploaded image."

        results = face_recognition.compare_faces([reference_encodings[0]], uploaded_encodings[0])
        return results[0], None if results[0] else "Face does not match."
    except Exception as e:
        return False, f"Face match error: {str(e)}"


def is_face_match(reference_path, uploaded_file, tolerance=0.6, num_jitters=1, model="cnn"):
    """
    Enhanced face matching with configurable parameters

    Args:
        reference_path: Path to reference image
        uploaded_file: Uploaded image file object
        tolerance: How much distance between faces to consider a match (lower = stricter)
                   Default 0.6 is good balance, 0.5 is stricter, 0.7 is more lenient
        num_jitters: How many times to re-sample the face (higher = more accurate but slower)
        model: "hog" (faster, less accurate) or "cnn" (slower, more accurate)

    Returns:
        Tuple: (match_status: bool, message: str or None)
    """
    try:
        # Load and check reference image
        reference_image = face_recognition.load_image_file(reference_path)
        reference_encodings = face_recognition.face_encodings(
            reference_image,
            num_jitters=num_jitters,
            model=model
        )
        if not reference_encodings:
            return False, "No face found in reference image."
        if len(reference_encodings) > 1:
            return False, "Multiple faces found in reference image. Only one face allowed."

        # Load and check uploaded image
        uploaded_image = face_recognition.load_image_file(uploaded_file)
        uploaded_encodings = face_recognition.face_encodings(
            uploaded_image,
            num_jitters=num_jitters,
            model=model
        )
        if not uploaded_encodings:
            return False, "No face found in uploaded image."
        if len(uploaded_encodings) > 1:
            return False, "Multiple faces found in uploaded image. Only one face allowed."

        # Compare faces with distance measurement
        face_distances = face_recognition.face_distance(
            [reference_encodings[0]],
            uploaded_encodings[0]
        )
        match = face_distances[0] <= tolerance

        # Return match status with confidence level
        confidence = 1 - face_distances[0]
        if match:
            return True, f"Match (confidence: {confidence:.2%})"
        else:
            return False, f"No match (confidence: {confidence:.2%})"

    except Exception as e:
        return False, f"Face match error: {str(e)}"




class FaceRecognitionValidationMixin:
    """Mixin for validating an uploaded photo against a reference photo"""

    def validate_face(self, form):
        """Validate face match"""
        employee = Employee.objects.get(user=self.request.user)
        reference_photo_path = employee.reference_photo.path
        uploaded_photo = form.cleaned_data['photo']
        uploaded_photo_file = uploaded_photo.file

        is_match, error = is_face_match(reference_photo_path, uploaded_photo_file)
        if not is_match:
            return False, error or "Face not matched"
        return True, None

