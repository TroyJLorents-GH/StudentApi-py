ROLE_DEFAULTS = {
    "admin": {
        "assignment_adder": True,
        "applications": True,
        "phd_applications": True,
        "student_summary_page": True,
        "bulk_upload_assignments": True,
        "manage_assignments": True,
        "login": True,
        "master_dashboard": True,
        "faculty_dashboard": True,
        "program_chair_uploads": True,
        "faculty_quickassign": True,
        "faculty_grader_uploads": True,
        "analytics": True,
        "chat": True,
    },
    "program_chair": {
        "assignment_adder": True,
        "applications": True,
        "phd_applications": False,
        "student_summary_page": True,
        "bulk_upload_assignments": True,
        "manage_assignments": False,
        "login": True,
        "master_dashboard": False,
        "faculty_dashboard": True,
        "program_chair_uploads": True,
        "faculty_quickassign": False,
        "faculty_grader_uploads": False,
        "analytics": False,
        "chat": False,
    },
    "faculty_grader": {
        "assignment_adder": False,
        "applications": True,
        "phd_applications": False,
        "student_summary_page": False,
        "bulk_upload_assignments": False,
        "manage_assignments": False,
        "login": True,
        "master_dashboard": False,
        "faculty_dashboard": True,
        "program_chair_uploads": False,
        "faculty_quickassign": True,
        "faculty_grader_uploads": True,
        "analytics": False,
        "chat": False,
    },
    "default": {
        "assignment_adder": False,
        "applications": False,
        "phd_applications": False,
        "student_summary_page": False,
        "bulk_upload_assignments": False,
        "manage_assignments": False,
        "login": True,
        "master_dashboard": False,
        "faculty_dashboard": False,
        "program_chair_uploads": False,
        "faculty_quickassign": False,
        "faculty_grader_uploads": False,
        "analytics": False,
        "chat": False,
    },
}


def merged_perms(role: str, row: dict | None) -> dict:
    """
    Start with role defaults (if any), then overlay ANY boolean keys from row.
    This makes 'custom' work because it has no defaults; we just take the row flags.
    """
    out = ROLE_DEFAULTS.get(role, {}).copy()
    if row:
        for k, v in row.items():
            if isinstance(v, bool):
                out[k] = v
    out["is_admin"] = (role == "admin")
    return out
