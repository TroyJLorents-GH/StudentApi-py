from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from fastapi.responses import StreamingResponse
import csv
import io

from models.assignment import StudentClassAssignment
from schemas.assignment_dto import StudentAssignmentUpdateDto
from database import get_db
from utils.assignment_utils import calculate_compensation, compute_cost_center_key
from schemas.assignment_schema import StudentClassAssignmentCreate
from schemas.assignment import StudentClassAssignmentRead
from fastapi.encoders import jsonable_encoder
from models.student import StudentLookup


router = APIRouter(prefix="/api/StudentClassAssignment", tags=["StudentClassAssignment"])


# GET all
@router.get("/", response_model=List[StudentClassAssignmentRead])
def get_assignments(db: Session = Depends(get_db)):
    return db.query(StudentClassAssignment).all()


@router.get("/template")
def download_template():
    headers = [
        "Position", "FultonFellow", "WeeklyHours", "Student_ID", "First_Name",
        "Last_Name", "Email", "EducationLevel", "Subject", "CatalogNum",
        "InstructorFirstName", "InstructorLastName", "ClassSession", "ClassNum",
        "Term", "Location", "Campus", "AcadCareer"
    ]
    example_row = [
        "IA/TA/Grader", "Yes/No", "5/10/15/20", "10 digit Id", "Name",
        "Last Name", "email@xxx.edu", "MS/PHD", "CSE/CIS/IEE", "100-700",
        "First Name", "Last Name", "A/B/C", "12345", "2254",
        "TEMPE", "TEMPE", "UGRD/GRAD"
    ]

    csv_content = ",".join(headers) + "\n" + ",".join(example_row) + "\n"
    # Use StreamingResponse to return a downloadable file
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=BulkUploadTemplate.csv"
        }
    )

# GET by ID
@router.get("/{assignment_id}", response_model=dict)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(StudentClassAssignment).filter_by(Id=assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


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
        # Read file content as text
        content = file.file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read CSV file.")

    records = []
    now = datetime.now(timezone.utc)

    for row in csv_reader:
        if not isinstance(row, dict):
            raise HTTPException(status_code=400, detail="CSV row is not a dictionary.")

        row["CreatedAt"] = now
        row["Term"] = "2254"

        try:
            row["WeeklyHours"] = int(row.get("WeeklyHours", 0))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid WeeklyHours value: {row.get('WeeklyHours')}")

        row["Compensation"] = calculate_compensation(row)
        row["CostCenterKey"] = compute_cost_center_key(row)

        if row.get("FultonFellow") == "Yes":
            student_id = row.get("Student_ID")
            student = db.query(StudentLookup).filter(StudentLookup.Student_ID == student_id).first()
            if student:
                row["cur_gpa"] = student.Current_GPA
                row["cum_gpa"] = student.Cumulative_GPA

        # Create SQLAlchemy obj
        try:
            record = StudentClassAssignment(**row)
            records.append(record)
        except TypeError as e:
            raise HTTPException(status_code=422, detail=f"Error creating assignment object: {e}")

    db.bulk_save_objects(records)
    db.commit()

    return {"message": f"{len(records)} records uploaded successfully."}



