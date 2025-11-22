from .upload_paths import PathAndRename

UPLOAD_PATHS = {
    "course_images": PathAndRename("course_materials/"),
    "profile_photos": PathAndRename("profile_photos/"),
    "student_cvs": PathAndRename("student_cvs/"),
    "proof_docs": PathAndRename("proof_docs/"),
    "misc": PathAndRename("uploads/"),
    "photos_student": PathAndRename("student_photos/"),
    "cv_or_resume": PathAndRename("student_cvs/"),
    "passed_record": PathAndRename("student_record/"),
    "birth_certificate": PathAndRename("birth_certificate/"),
    "card_id": PathAndRename("card_id/"),
    "proof_of_residency": PathAndRename("proof_residency/"),
    "school_certificate": PathAndRename("school_certificate/"),
    "signature":PathAndRename("user_signature/"),
    'logos':PathAndRename('Logos/'),
    'default':PathAndRename('Default/'),
    'reference_photos': PathAndRename('Reference_photos/'),
    'clock_in_photo':PathAndRename('Clock_in_photo/'),
    'break_start_photo':PathAndRename('Break_start_photo/'),
    'break_end_photo':PathAndRename('Break_end_photo/'),
    'clock_out_photo':PathAndRename('Clock_out_photo/'),
}
