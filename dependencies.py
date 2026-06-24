from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user_access import UserAccess
from utils.rbac import merged_perms


def current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    """
    Get current user from dev cookie auth.
    Reads the 'auth' cookie set by /api/dev-impersonate.
    """
    cookie_asurite = (request.cookies.get("auth") or "").lower().strip()
    if not cookie_asurite:
        return {"asurite": None, "role": "guest", "is_admin": False, "perms": {}}

    row = db.get(UserAccess, cookie_asurite)
    if not row:
        return {"asurite": cookie_asurite, "role": "guest", "is_admin": False, "perms": {}}

    flags = {
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
        "analytics": bool(row.analytics),
        "chat": bool(row.chat),
    }
    perms = merged_perms(row.role, flags)

    return {
        "asurite": row.asu_id,
        "role": row.role,
        "is_admin": row.role == "admin",
        "perms": perms,
        "email": row.email,
        "name": row.name,
    }


def require_perm(flag: str):
    """Dependency factory: allow admins or users whose perms[flag] is truthy; else 403."""
    def _dep(user: dict = Depends(current_user)) -> dict:
        perms = user.get("perms") or {}
        if user.get("role") == "admin" or user.get("is_admin") or perms.get(flag):
            return user
        raise HTTPException(status_code=403, detail="forbidden")
    return _dep
