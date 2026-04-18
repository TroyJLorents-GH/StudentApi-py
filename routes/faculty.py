from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os

from database import get_db
from models.assignment import StudentClassAssignment
from dependencies import current_user

ACTIVE_TERM = os.getenv("ACTIVE_TERM", "2254")

router = APIRouter(prefix="/api/faculty", tags=["faculty"])


class FacultyAssignmentRead(BaseModel):
    Id: int
    Student_ID: int
    ASUrite: Optional[str] = None
    Position: str
    WeeklyHours: int
    FultonFellow: str
    Email: str
    EducationLevel: str
    Subject: str
    CatalogNum: int
    ClassSession: str
    ClassNum: str
    Term: str
    InstructorFirstName: str
    InstructorLastName: str
    Location: str
    Campus: str
    AcadCareer: str
    First_Name: Optional[str] = None
    Last_Name: Optional[str] = None
    cum_gpa: Optional[float] = None
    cur_gpa: Optional[float] = None
    ImportedBy: Optional[str] = None

    class Config:
        from_attributes = True


def require_perm(user: dict, flag: str) -> None:
    if not user or not user.get("perms", {}).get(flag, False):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/student-assignments", response_model=List[FacultyAssignmentRead])
def get_faculty_assignments(
    db: Session = Depends(get_db),
    user: dict = Depends(current_user),
):
    require_perm(user, "faculty_dashboard")

    rows = db.query(StudentClassAssignment).filter(
        StudentClassAssignment.Term == ACTIVE_TERM,
        StudentClassAssignment.Instructor_Edit.is_(None)
    ).all()

    safe = []
    for r in rows:
        safe.append({
            "Id": r.Id,
            "Student_ID": r.Student_ID,
            "ASUrite": r.ASUrite,
            "Position": r.Position,
            "WeeklyHours": r.WeeklyHours,
            "FultonFellow": r.FultonFellow,
            "Email": r.Email,
            "EducationLevel": r.EducationLevel,
            "Subject": r.Subject,
            "CatalogNum": r.CatalogNum,
            "ClassSession": r.ClassSession,
            "ClassNum": r.ClassNum,
            "Term": r.Term,
            "InstructorFirstName": r.InstructorFirstName,
            "InstructorLastName": r.InstructorLastName,
            "Location": r.Location,
            "Campus": r.Campus,
            "AcadCareer": r.AcadCareer,
            "First_Name": getattr(r, "First_Name", None),
            "Last_Name": getattr(r, "Last_Name", None),
            "cum_gpa": getattr(r, "cum_gpa", None),
            "cur_gpa": getattr(r, "cur_gpa", None),
            "ImportedBy": getattr(r, "ImportedBy", None),
        })
    return safe
