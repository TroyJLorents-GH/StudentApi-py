from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import csv
import io
from fastapi.responses import StreamingResponse


from models.assignment import StudentClassAssignment
from schemas.assignment_dto import StudentAssignmentUpdateDto
from database import get_db
from utils.assignment_utils import calculate_compensation, compute_cost_center_key, infer_acad_career
from schemas.assignment_schema import StudentClassAssignmentCreate
from schemas.assignment import StudentClassAssignmentRead
from models.student import StudentLookup
from fastapi.encoders import jsonable_encoder


router = APIRouter(prefix="/api/StudentClassAssignment", tags=["StudentClassAssignment"])


# GET all
@router.get("/", response_model=List[StudentClassAssignmentRead])
def get_assignments(db: Session = Depends(get_db)):
    return db.query(StudentClassAssignment).all()


@router.get("/template")
def download_template():
    headers = [
        "Position", "FultonFellow", "WeeklyHours", "Student_ID (ID number OR ASUrite accepted)", "First_Name",
        "Last_Name", "Email", "EducationLevel", "Subject", "CatalogNum",
        "InstructorFirstName", "InstructorLastName", "InstructorID", "ClassSession", "ClassNum",
        "Location", "Campus"
    ]
    csv_content = ",".join(headers) + "\n"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=BulkUploadTemplate.csv"}
    )


# GET by ID
@router.get("/{assignment_id}", response_model=dict)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(StudentClassAssignment).filter_by(Id=assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {
        "Id": assignment.Id,
        "Position_Number": assignment.Position_Number,
        "SSN_Sent": assignment.SSN_Sent,
        "Offer_Sent": assignment.Offer_Sent,
        "Offer_Signed": assignment.Offer_Signed,
    }


# GET total hours by student
@router.get("/totalhours/{student_id}", response_model=int)
def get_total_hours(student_id: int, db: Session = Depends(get_db)):
    total = db.query(StudentClassAssignment).filter_by(Student_ID=student_id).with_entities(
        StudentClassAssignment.WeeklyHours
    ).all()

    return sum([a[0] for a in total])


# POST single assignment
@router.post("/", status_code=201)
def create_assignment(assignment: StudentClassAssignmentCreate, db: Session = Depends(get_db)):
    new_assignment = StudentClassAssignment(**assignment.dict())
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    return {"message": "Assignment created", "id": new_assignment.Id}


# PUT update assignment
@router.put("/{assignment_id}", status_code=204)
def update_assignment(assignment_id: int, update_data: StudentAssignmentUpdateDto, db: Session = Depends(get_db)):
    assignment = db.query(StudentClassAssignment).filter_by(Id=assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)

    db.commit()
    return


# POST bulk upload from CSV
@router.post("/upload")
def upload_assignments(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. CSV required.")

    try:
        content = file.file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read CSV file.")

    records = []
    now = datetime.now(timezone.utc)

    for row in csv_reader:
        input_id = (row.get("Student_ID (ID number OR ASUrite accepted)") or "").strip()

        # Determine if input is numeric (Student_ID) or ASUrite
        student = None
        if input_id.isdigit():
            student = db.query(StudentLookup).filter(StudentLookup.Student_ID == int(input_id)).first()
        elif input_id:
            student = db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(input_id)).first()

        if not student:
            raise HTTPException(status_code=422, detail=f"No student found for: {input_id}")

        # Always set both fields explicitly, so row matches your DB model
        row["Student_ID"] = student.Student_ID
        row["ASUrite"] = student.ASUrite

        # Rest of your field mapping/logic (keep these as you have them!)
        row["CreatedAt"] = now
        row["Term"] = "2257"

        try:
            row["WeeklyHours"] = int(row.get("WeeklyHours", 0))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid WeeklyHours value: {row.get('WeeklyHours')}")

        row["AcadCareer"] = infer_acad_career(row)
        row["CostCenterKey"] = compute_cost_center_key(row)
        row["Compensation"] = calculate_compensation(row)

        if str(row.get("FultonFellow", "")).strip().lower() == "yes":
            row["cur_gpa"] = student.Current_GPA
            row["cum_gpa"] = student.Cumulative_GPA
        else:
            row["cur_gpa"] = None
            row["cum_gpa"] = None

        # Only include columns that exist in your model
        allowed_fields = {c.name for c in StudentClassAssignment.__table__.columns}
        clean_row = {k: v for k, v in row.items() if k in allowed_fields}

        try:
            record = StudentClassAssignment(**clean_row)
            records.append(record)
        except TypeError as e:
            raise HTTPException(status_code=422, detail=f"Error creating assignment object: {e}")

    db.bulk_save_objects(records)
    db.commit()
    return {"message": f"{len(records)} records uploaded successfully."}





# NEW: Get assignment summary for a student (by Student_ID or ASUrite)
@router.get("/student-summary/{identifier}")
def get_assignment_summary(identifier: str, db: Session = Depends(get_db)):
    # Lookup student by Student_ID or ASUrite
    if identifier.isdigit():
        student = db.query(StudentLookup).filter(StudentLookup.Student_ID == int(identifier)).first()
    else:
        student = db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(identifier)).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get all assignments for this student
    assignments = db.query(StudentClassAssignment).filter(
        StudentClassAssignment.Student_ID == student.Student_ID
    ).all()

    # Tally hours by session
    session_hours = {"A": 0, "B": 0, "C": 0}
    assignment_list = []
    for a in assignments:
        session = (a.ClassSession or "").strip().upper()
        if session in session_hours:
            session_hours[session] += a.WeeklyHours
        assignment_list.append({
            "Position": a.Position,
            "WeeklyHours": a.WeeklyHours,
            "ClassSession": a.ClassSession,
            "Subject": a.Subject,
            "CatalogNum": a.CatalogNum,
            "ClassNum": a.ClassNum,
            "InstructorName": f"{a.InstructorFirstName} {a.InstructorLastName}"
        })

    # Compose response
    return {
        "StudentName": f"{student.First_Name or ''} {student.Last_Name or ''}".strip(),
        "ASUrite": student.ASUrite,
        "Student_ID": student.Student_ID,
        "Position": assignments[0].Position if assignments else None,
        "FultonFellow": assignments[0].FultonFellow if assignments else None,
        "EducationLevel": assignments[0].EducationLevel if assignments else None,
        "sessionA": session_hours["A"],
        "sessionB": session_hours["B"],
        "sessionC": session_hours["C"],
        "assignments": assignment_list
    }