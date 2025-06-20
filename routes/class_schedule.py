from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.class_schedule import ClassSchedule2254
# from models.class_lookup import ClassLookup  # Assuming you have a second table for 2251


router = APIRouter(prefix="/api/class", tags=["Class"])


# GET /subjects?term=2254
@router.get("/subjects", response_model=List[str])
def get_subjects(term: str = Query(...), db: Session = Depends(get_db)):
    if term == "2254":
        return list({
            c.Subject for c in db.query(ClassSchedule2254.Subject).filter_by(Term=term)
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid term value.")


# GET /catalog?term=2254&subject=XYZ
@router.get("/catalog", response_model=List[str])
def get_catalog_numbers(term: str, subject: str, db: Session = Depends(get_db)):
    if term == "2254":
        return list({
            str(c.CatalogNum) for c in db.query(ClassSchedule2254).filter_by(Term=term, Subject=subject)
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid term value.")


# GET /classnumbers?term=2254&subject=XYZ&catalogNum=123
@router.get("/classnumbers", response_model=List[str])
def get_class_numbers(term: str, subject: str, catalogNum: str, db: Session = Depends(get_db)):
    try:
        catalog_int = int(catalogNum)
    except ValueError:
        raise HTTPException(status_code=400, detail="CatalogNum must be numeric.")

    if term == "2254":
        return list({
            c.ClassNum for c in db.query(ClassSchedule2254).filter_by(Term=term, Subject=subject, CatalogNum=catalogNum)
        })
    else:
        raise HTTPException(status_code=400, detail="Invalid term value.")


# GET /details/{classNum}?term=2254
@router.get("/details/{classNum}")
def get_class_details(classNum: str, term: str, db: Session = Depends(get_db)):
    if term == "2254":
        class_obj = db.query(ClassSchedule2254).filter_by(ClassNum=classNum, Term=term).first()
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
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid term value.")
