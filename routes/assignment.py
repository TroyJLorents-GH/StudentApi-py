from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import csv
import io
from fastapi.responses import StreamingResponse


from models.assignment import StudentClassAssignment
from models.class_schedule import ClassSchedule2254
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
    return db.query(StudentClassAssignment).filter(StudentClassAssignment.Instructor_Edit.is_(None)).all()


@router.get("/template")
def download_template():
    headers = [
        "Position", "FultonFellow", "WeeklyHours", "Student_ID (ID number OR ASUrite accepted)", "ClassNum"
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
    new_assignment = StudentClassAssignment(**assignment.model_dump())
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
# @router.post("/upload")
# def upload_assignments(file: UploadFile = File(...), db: Session = Depends(get_db)):
#     if not file.filename.endswith(".csv"):
#         raise HTTPException(status_code=400, detail="Invalid file type. CSV required.")
#
#     try:
#         content = file.file.read().decode("utf-8")
#         csv_reader = csv.DictReader(io.StringIO(content))
#     except Exception:
#         raise HTTPException(status_code=400, detail="Failed to read CSV file.")
#
#     records = []
#     now = datetime.now(timezone.utc)
#
#     for row in csv_reader:
#         input_id = (row.get("Student_ID (ID number OR ASUrite accepted)") or "").strip()
#
#         # Determine if input is numeric (Student_ID) or ASUrite
#         student = None
#         if input_id.isdigit():
#             student = db.query(StudentLookup).filter(StudentLookup.Student_ID == int(input_id)).first()
#         elif input_id:
#             student = db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(input_id)).first()
#
#         if not student:
#             raise HTTPException(status_code=422, detail=f"No student found for: {input_id}")
#
#         # Always set both fields explicitly, so row matches your DB model
#         row["Student_ID"] = student.Student_ID
#         row["ASUrite"] = student.ASUrite
#
#         # Rest of your field mapping/logic (keep these as you have them!)
#         row["CreatedAt"] = now
#         row["Term"] = "2257"
#
#         try:
#             row["WeeklyHours"] = int(row.get("WeeklyHours", 0))
#         except ValueError:
#             raise HTTPException(status_code=422, detail=f"Invalid WeeklyHours value: {row.get('WeeklyHours')}")
#
#         row["AcadCareer"] = infer_acad_career(row)
#         row["CostCenterKey"] = compute_cost_center_key(row)
#         row["Compensation"] = calculate_compensation(row)
#
#         if str(row.get("FultonFellow", "")).strip().lower() == "yes":
#             row["cur_gpa"] = student.Current_GPA
#             row["cum_gpa"] = student.Cumulative_GPA
#         else:
#             row["cur_gpa"] = None
#             row["cum_gpa"] = None
#
#         # Only include columns that exist in your model
#         allowed_fields = {c.name for c in StudentClassAssignment.__table__.columns}
#         clean_row = {k: v for k, v in row.items() if k in allowed_fields}
#
#         try:
#             record = StudentClassAssignment(**clean_row)
#             records.append(record)
#         except TypeError as e:
#             raise HTTPException(status_code=422, detail=f"Error creating assignment object: {e}")
#
#     db.bulk_save_objects(records)
#     db.commit()
#     return {"message": f"{len(records)} records uploaded successfully."}


@router.post("/upload")
def upload_assignments(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="CSV or XLSX required.")
    try:
        # Read CSV (Excel not handled in this backend example, but could be added)
        content = file.file.read().decode("utf-8-sig")
        csv_reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not read CSV: " + str(e))

    records = []
    now = datetime.now(timezone.utc)
    required_fields = ["Position", "WeeklyHours", "Student_ID (ID number OR ASUrite accepted)", "ClassNum"]

    for idx, row in enumerate(csv_reader, start=2):
        # --- Validate required fields (except FultonFellow, which is optional) ---
        for field in required_fields:
            if field not in row or not str(row[field]).strip():
                raise HTTPException(422, f"Missing field '{field}' in row {idx}")

        # --- Set FultonFellow to 'No' if it's blank or empty or missing ---
        fulton = str(row.get("FultonFellow", "")).strip()
        row["FultonFellow"] = fulton if fulton else "No"

        # --- Student Lookup ---
        student_id_or_asurite = row["Student_ID (ID number OR ASUrite accepted)"].strip()
        student = None
        if student_id_or_asurite.isdigit():
            student = db.query(StudentLookup).filter(StudentLookup.Student_ID == int(student_id_or_asurite)).first()
        else:
            student = db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(student_id_or_asurite)).first()
        if not student:
            raise HTTPException(422, f"Student '{student_id_or_asurite}' not found (row {idx})")

        # --- Class Lookup ---
        class_num = row["ClassNum"].strip()
        class_obj = db.query(ClassSchedule2254).filter_by(ClassNum=class_num).first()
        if not class_obj:
            raise HTTPException(422, f"ClassNum '{class_num}' not found (row {idx})")

        # --- Compose calculated fields ---
        weekly_hours = int(row["WeeklyHours"])
        position = row["Position"]
        fulton_fellow = row["FultonFellow"]
        session = class_obj.Session

        compensation = calculate_compensation({
            "WeeklyHours": weekly_hours,
            "Position": position,
            "EducationLevel": student.Degree,
            "FultonFellow": fulton_fellow,
            "ClassSession": session
        })
        cost_center = compute_cost_center_key({
            "Position": position,
            "Location": class_obj.Location,
            "Campus": class_obj.Campus,
            "AcadCareer": class_obj.AcadCareer
        })

        # --- Compose assignment object ---
        assignment = StudentClassAssignment(
            Student_ID=student.Student_ID,
            ASUrite=student.ASUrite,
            Position=position,
            FultonFellow=fulton_fellow,
            WeeklyHours=weekly_hours,
            Email=student.ASU_Email_Adress,
            First_Name=student.First_Name,
            Last_Name=student.Last_Name,
            EducationLevel=student.Degree,
            Subject=class_obj.Subject,
            CatalogNum=class_obj.CatalogNum,
            ClassSession=class_obj.Session,
            ClassNum=class_num,
            Term=class_obj.Term,
            InstructorFirstName=class_obj.InstructorFirstName,
            InstructorLastName=class_obj.InstructorLastName,
            InstructorID=class_obj.InstructorID,
            Location=class_obj.Location,
            Campus=class_obj.Campus,
            AcadCareer=class_obj.AcadCareer,
            CostCenterKey=cost_center,
            Compensation=compensation,
            CreatedAt=now,
            cum_gpa=float(student.Cumulative_GPA or 0),
            cur_gpa=float(student.Current_GPA or 0),
        )
        records.append(assignment)

    db.bulk_save_objects(records)
    db.commit()
    return {"message": f"{len(records)} assignments uploaded successfully."}


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
        StudentClassAssignment.Student_ID == student.Student_ID,
        StudentClassAssignment.Instructor_Edit.is_(None)
    ).all()

    # Tally hours by session
    session_hours = {"A": 0, "B": 0, "C": 0}
    assignment_list = []
    for a in assignments:
        session = (a.ClassSession or "").strip().upper()
        if session in session_hours:
            session_hours[session] += a.WeeklyHours
        assignment_list.append({
            "Id": a.Id,
            "Position": a.Position,
            "WeeklyHours": a.WeeklyHours,
            "ClassSession": a.ClassSession,
            "Subject": a.Subject,
            "CatalogNum": a.CatalogNum,
            "ClassNum": a.ClassNum,
            "InstructorName": f"{a.InstructorFirstName} {a.InstructorLastName}",
            "AcadCareer": a.AcadCareer,
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




@router.post("/bulk-edit")
def bulk_edit_assignments(
    updates: dict,
    db: Session = Depends(get_db)
):
    """
    Request body format:
    {
        "updates": [{ "id": 123, "Position": ..., "WeeklyHours": ..., "ClassNum": ...}, ...],
        "deletes": [456, 789],
        "studentId": "ASUrite or Student_ID"
    }
    """
    student_id = updates.get("studentId")
    update_rows = updates.get("updates", [])
    delete_ids = updates.get("deletes", [])

    # Find student
    if not student_id:
        raise HTTPException(400, "No studentId provided")
    if str(student_id).isdigit():
        student = db.query(StudentLookup).filter(StudentLookup.Student_ID == int(student_id)).first()
    else:
        student = db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(student_id)).first()
    if not student:
        raise HTTPException(404, "Student not found")

    # 1. Handle updates/edits
    for edit in update_rows:
        orig_id = edit["id"]
        orig = db.query(StudentClassAssignment).filter_by(Id=orig_id).first()
        if not orig:
            continue
        # Mark original as edited
        orig.Instructor_Edit = "Y"
        db.add(orig)
        db.flush()

        class_obj = None
        if "ClassNum" in edit and edit["ClassNum"] != orig.ClassNum:
            from models.class_schedule import ClassSchedule2254
            class_obj = db.query(ClassSchedule2254).filter_by(ClassNum=edit["ClassNum"], Term=orig.Term).first()
            if not class_obj:
                raise HTTPException(404, f"ClassNum {edit['ClassNum']} not found")

        # Always recalculate compensation & cost center based on new info
        comp = calculate_compensation({
            "WeeklyHours": edit["WeeklyHours"],
            "Position": edit["Position"],
            "EducationLevel": orig.EducationLevel,
            "FultonFellow": orig.FultonFellow,
            "ClassSession": class_obj.Session if class_obj else orig.ClassSession
        })
        cost_center = compute_cost_center_key({
            "Position": edit["Position"],
            "Location": class_obj.Location if class_obj else orig.Location,
            "Campus": class_obj.Campus if class_obj else orig.Campus,
            "AcadCareer": class_obj.AcadCareer if class_obj else orig.AcadCareer
        })

        new_assign = StudentClassAssignment(
            Student_ID=orig.Student_ID,
            ASUrite=orig.ASUrite,
            Position=edit["Position"],
            WeeklyHours=edit["WeeklyHours"],
            FultonFellow=orig.FultonFellow,
            Email=orig.Email,
            EducationLevel=orig.EducationLevel,
            Subject=class_obj.Subject if class_obj else orig.Subject,
            CatalogNum=class_obj.CatalogNum if class_obj else orig.CatalogNum,
            ClassSession=class_obj.Session if class_obj else orig.ClassSession,
            ClassNum=edit["ClassNum"] if "ClassNum" in edit else orig.ClassNum,
            Term=orig.Term,
            InstructorFirstName=class_obj.InstructorFirstName if class_obj else orig.InstructorFirstName,
            InstructorLastName=class_obj.InstructorLastName if class_obj else orig.InstructorLastName,
            InstructorID=class_obj.InstructorID if class_obj else orig.InstructorID,
            Compensation=comp,
            Location=class_obj.Location if class_obj else orig.Location,
            Campus=class_obj.Campus if class_obj else orig.Campus,
            AcadCareer=class_obj.AcadCareer if class_obj else orig.AcadCareer,
            CostCenterKey=cost_center,
            cur_gpa=orig.cur_gpa,
            cum_gpa=orig.cum_gpa,
            CreatedAt=datetime.now(timezone.utc),
            Instructor_Edit=None,  # Not edited yet
            First_Name=orig.First_Name,
            Last_Name=orig.Last_Name,
            Position_Number=orig.Position_Number,
            SSN_Sent=orig.SSN_Sent,
            Offer_Sent=orig.Offer_Sent,
            Offer_Signed=orig.Offer_Signed
        )
        db.add(new_assign)
    # 2. Handle deletions
    for del_id in delete_ids:
        orig = db.query(StudentClassAssignment).filter_by(Id=del_id).first()
        if orig:
            orig.Instructor_Edit = "D"
            db.add(orig)
    db.commit()
    return {"status": "success"}