from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, not_
from models.assignment import StudentClassAssignment
from database import get_db
from schemas.manage_assignments_dto import ManageAssignmentUpdateDTO
from utils.assignment_utils import calculate_compensation, compute_cost_center_key, infer_acad_career

router = APIRouter(
    prefix="/api/manage-assignments",
    tags=["manage-assignments"]
)

@router.get("/by-instructor/{instructor_id}")
def get_assignments_by_instructor(instructor_id: int, db: Session = Depends(get_db)):
    # Only include assignments where Instructor_Edit is not 'Y' or 'D' (or is null/None)
    assignments = db.query(StudentClassAssignment).filter(
        StudentClassAssignment.InstructorID == instructor_id,
        or_(
            StudentClassAssignment.Instructor_Edit == None,  # Allow None/null
            not_(StudentClassAssignment.Instructor_Edit.in_(['Y', 'D']))  # Exclude 'Y' and 'D'
        )
    ).all()
    # Prepare return dict as before
    return [
        {
            "Id": a.Id,
            "Student_ID": a.Student_ID,
            "ASUrite": a.ASUrite,
            "First_Name": a.First_Name,
            "Last_Name": a.Last_Name,
            "Position": a.Position,
            "WeeklyHours": a.WeeklyHours,
            "FultonFellow": a.FultonFellow,
            "Email": a.Email,
            "EducationLevel": a.EducationLevel,
            "Subject": a.Subject,
            "CatalogNum": a.CatalogNum,
            "ClassSession": a.ClassSession,
            "ClassNum": a.ClassNum,
            "Term": a.Term,
            "InstructorFirstName": a.InstructorFirstName,
            "InstructorLastName": a.InstructorLastName,
            "InstructorID": a.InstructorID,
            "Location": a.Location,
            "Campus": a.Campus,
            "AcadCareer": a.AcadCareer,
        }
        for a in assignments
    ]

@router.put("/{assignment_id}")
def update_assignment(
    assignment_id: int,
    update: ManageAssignmentUpdateDTO,
    db: Session = Depends(get_db)
):
    assignment = db.query(StudentClassAssignment).filter(StudentClassAssignment.Id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Track which fields changed (for recomputation)
    compensation_fields = ["Position", "WeeklyHours", "EducationLevel", "FultonFellow", "ClassSession"]
    costcenter_fields = ["Position", "Location", "Campus", "AcadCareer"]

    changed = set()

    # Update only the provided fields
    for field, value in update.dict(exclude_unset=True).items():
        setattr(assignment, field, value)
        changed.add(field)

    # Update AcadCareer if CatalogNum changed
    if "CatalogNum" in changed:
        assignment.AcadCareer = infer_acad_career({"CatalogNum": assignment.CatalogNum})

    # Recompute compensation if any relevant fields changed
    if any(f in changed for f in compensation_fields):
        assignment.Compensation = calculate_compensation({
            "WeeklyHours": assignment.WeeklyHours,
            "Position": assignment.Position,
            "EducationLevel": assignment.EducationLevel,
            "FultonFellow": assignment.FultonFellow,
            "ClassSession": assignment.ClassSession
        })

    # Recompute CostCenterKey if any relevant fields changed
    if any(f in changed for f in costcenter_fields) or "AcadCareer" in changed:
        assignment.CostCenterKey = compute_cost_center_key({
            "Position": assignment.Position,
            "Location": assignment.Location,
            "Campus": assignment.Campus,
            "AcadCareer": assignment.AcadCareer
        })

    db.commit()
    db.refresh(assignment)
    return {
        "message": "Assignment updated successfully.",
        "assignment": {
            "Id": assignment.Id,
            "WeeklyHours": assignment.WeeklyHours,
            "Position": assignment.Position,
            "FultonFellow": assignment.FultonFellow,
            "Subject": assignment.Subject,
            "CatalogNum": assignment.CatalogNum,
            "ClassSession": assignment.ClassSession,
            "ClassNum": assignment.ClassNum,
            "Compensation": assignment.Compensation,
            "CostCenterKey": assignment.CostCenterKey,
            # Add more fields as needed
        }
    }