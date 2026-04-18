import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user_access import UserAccess
from models.admin_audit_log import AdminAuditLog
from utils.rbac import ROLE_DEFAULTS, merged_perms

router = APIRouter(prefix="/api/admin", tags=["admin-users"])


def log_audit_action(db: Session, admin_user: str, action_type: str, status: str, summary: str, details: dict = None):
    """Log an admin action to the audit log table."""
    try:
        details_json = json.dumps(details) if details else "{}"
        audit_log = AdminAuditLog(
            admin_user=admin_user,
            action_type=action_type,
            status=status,
            summary=summary,
            details=details_json
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        print(f"Audit log error: {str(e)}")


def require_admin(request: Request, db: Session = Depends(get_db)):
    """Check dev cookie for admin role."""
    cookie_asurite = (request.cookies.get("auth") or "").lower().strip()
    if cookie_asurite:
        row = db.get(UserAccess, cookie_asurite)
        if row and row.role == "admin":
            return cookie_asurite
    raise HTTPException(status_code=403, detail="forbidden")


def serialize_user_access(r: UserAccess) -> dict:
    base = {
        "asu_id": r.asu_id,
        "role": r.role,
        "assignment_adder": bool(r.assignment_adder),
        "applications": bool(r.applications),
        "phd_applications": bool(r.phd_applications),
        "student_summary_page": bool(r.student_summary_page),
        "bulk_upload_assignments": bool(r.bulk_upload_assignments),
        "manage_assignments": bool(r.manage_assignments),
        "login": bool(r.login),
        "master_dashboard": bool(r.master_dashboard),
        "faculty_dashboard": bool(r.faculty_dashboard),
        "program_chair_uploads": bool(r.program_chair_uploads),
        "faculty_quickassign": bool(r.faculty_quickassign),
        "faculty_grader_uploads": bool(r.faculty_grader_uploads),
        "email": r.email,
        "emplid": r.emplid,
        "name": r.name,
        "position_title": r.position_title,
        "program": r.program,
    }
    row_dict = base.copy()
    base["perms"] = merged_perms(r.role, row_dict)
    return base


@router.get("/users")
def list_users(db: Session = Depends(get_db), me: str = Depends(require_admin)):
    rows = db.query(UserAccess).all()
    return [serialize_user_access(r) for r in rows]


@router.post("/users")
def create_user(payload: dict, db: Session = Depends(get_db), me: str = Depends(require_admin)):
    asu_id = payload["asu_id"].lower()
    role = payload["role"]
    if db.get(UserAccess, asu_id):
        raise HTTPException(status_code=400, detail="asu_id exists")

    role_defaults = ROLE_DEFAULTS.get(role, {})
    flags = {k: bool(payload.get(k, role_defaults.get(k, False))) for k in ROLE_DEFAULTS["admin"].keys()}

    r = UserAccess(
        asu_id=asu_id,
        role=role,
        name=payload.get("name"),
        position_title=payload.get("position_title"),
        **flags
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return serialize_user_access(r)


@router.patch("/users/{asu_id}")
def update_user(asu_id: str, payload: dict, db: Session = Depends(get_db), me: str = Depends(require_admin)):
    r = db.get(UserAccess, asu_id.lower())
    if not r:
        raise HTTPException(status_code=404, detail="not found")

    if asu_id.lower() == me.lower():
        raise HTTPException(status_code=403, detail="Cannot modify your own user account. Ask another admin for help.")

    if "role" in payload:
        r.role = payload["role"]

    for k in ROLE_DEFAULTS["admin"].keys():
        if k in payload:
            setattr(r, k, bool(payload[k]))

    db.commit()
    db.refresh(r)

    log_audit_action(
        db,
        admin_user=me,
        action_type="user_modified",
        status="Success",
        summary=f"Modified user {asu_id}",
        details={
            "modified_user": asu_id,
            "new_role": r.role,
            "permissions_changed": list(payload.keys())
        }
    )

    return serialize_user_access(r)


@router.delete("/users/{asu_id}")
def delete_user(asu_id: str, db: Session = Depends(get_db), me: str = Depends(require_admin)):
    r = db.get(UserAccess, asu_id.lower())
    if not r:
        raise HTTPException(status_code=404, detail="not found")

    if asu_id.lower() == me.lower():
        raise HTTPException(status_code=403, detail="Cannot delete your own user account. Ask another admin for help.")

    db.delete(r)
    db.commit()

    log_audit_action(
        db,
        admin_user=me,
        action_type="user_deleted",
        status="Success",
        summary=f"Deleted user {asu_id}",
        details={"deleted_user": asu_id, "role": r.role}
    )

    return {"ok": True}


@router.get("/audit-logs")
def get_audit_logs(limit: int = 100, me: str = Depends(require_admin), db: Session = Depends(get_db)):
    """Retrieve audit logs for admin actions."""
    try:
        audit_logs = db.query(AdminAuditLog).order_by(AdminAuditLog.timestamp.desc()).limit(limit).all()

        logs = []
        for log in audit_logs:
            logs.append({
                "id": log.id,
                "admin_user": log.admin_user,
                "action_type": log.action_type,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "status": log.status,
                "summary": log.summary,
                "details": log.details if log.details else "{}"
            })

        return {
            "success": True,
            "logs": logs,
            "count": len(logs)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving audit logs: {str(e)}",
            "logs": []
        }
