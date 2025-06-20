from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.student import StudentLookup
from database import get_db

router = APIRouter(prefix="/api/StudentLookup", tags=["StudentLookup"])


@router.get("/{identifier}")
def get_student_by_id_or_asurite(identifier: str, db: Session = Depends(get_db)):
    student = None

    if identifier.isdigit():
        student = db.query(StudentLookup).filter(StudentLookup.Student_ID == int(identifier)).first()
    else:
        student = db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(identifier)).first()

    if student is None:
        raise HTTPException(status_code=404, detail=f"No student found with identifier: {identifier}")

    return student
