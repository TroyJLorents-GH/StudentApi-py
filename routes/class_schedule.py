from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.class_schedule import ClassSchedule


router = APIRouter(prefix="/api/class", tags=["Class"])


# GET /subjects?term=2261
@router.get("/subjects", response_model=List[str])
def get_subjects(term: str = Query(...), db: Session = Depends(get_db)):
    return list({
        c.Subject for c in db.query(ClassSchedule.Subject).filter_by(Term=term)
    })


# GET /catalog?term=2261&subject=XYZ
@router.get("/catalog", response_model=List[str])
def get_catalog_numbers(term: str, subject: str, db: Session = Depends(get_db)):
    return list({
        str(c.CatalogNum) for c in db.query(ClassSchedule).filter_by(Term=term, Subject=subject)
    })


# GET /classnumbers?term=2261&subject=XYZ&catalogNum=123
@router.get("/classnumbers", response_model=List[str])
def get_class_numbers(term: str, subject: str, catalogNum: str, db: Session = Depends(get_db)):
    try:
        catalog_int = int(catalogNum)
    except ValueError:
        raise HTTPException(status_code=400, detail="CatalogNum must be numeric.")

    return list({
        c.ClassNum for c in db.query(ClassSchedule).filter_by(Term=term, Subject=subject, CatalogNum=catalog_int)
    })


# GET /details/{classNum}?term=2261
@router.get("/details/{classNum}")
def get_class_details(classNum: str, term: str, db: Session = Depends(get_db)):
    class_obj = db.query(ClassSchedule).filter_by(ClassNum=classNum, Term=term).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return {
        "Session": class_obj.Session,
        "Term": class_obj.Term,
        "InstructorID": class_obj.InstructorID,
        "InstructorFirstName": class_obj.InstructorFirstName,
        "InstructorLastName": class_obj.InstructorLastName,
        "InstructorEmail": class_obj.InstructorEmail,
        "Location": class_obj.Location,
        "Campus": class_obj.Campus,
        "AcadCareer": class_obj.AcadCareer,
        "Subject": class_obj.Subject,
        "CatalogNum": class_obj.CatalogNum,
    }
