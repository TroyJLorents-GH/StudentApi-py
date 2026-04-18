from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_access import UserAccess
from utils.rbac import merged_perms


def get_user_and_perms(asurite: str) -> dict:
    """
    Load the user from dbo.user_access and return the shape the frontend expects.
    """
    db: Session = SessionLocal()
    try:
        row: UserAccess | None = db.get(UserAccess, asurite.lower())
        if not row:
            return {
                "asurite": asurite,
                "role": "default",
                "is_admin": False,
                "perms": merged_perms("default", {}),
            }

        row_flags = {
            "assignment_adder": bool(row.assignment_adder),
            "applications": bool(row.applications),
            "phd_applications": bool(row.phd_applications),
            "student_summary_page": bool(row.student_summary_page),
            "bulk_upload_assignments": bool(row.bulk_upload_assignments),
            "manage_assignments": bool(row.manage_assignments),
            "login": bool(row.login),
            "master_dashboard": bool(row.master_dashboard),
            "faculty_dashboard": bool(row.faculty_dashboard),
            "program_chair_uploads": bool(row.program_chair_uploads),
            "faculty_quickassign": bool(row.faculty_quickassign),
            "faculty_grader_uploads": bool(row.faculty_grader_uploads),
        }

        perms = merged_perms(row.role, row_flags)

        return {
            "asurite": row.asu_id,
            "role": row.role,
            "is_admin": row.role == "admin",
            "perms": perms,
            "email": row.email,
            "name": row.name,
        }
    finally:
        db.close()
