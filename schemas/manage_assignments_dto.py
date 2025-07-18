from pydantic import BaseModel
from typing import Optional

class ManageAssignmentUpdateDTO(BaseModel):
    WeeklyHours: Optional[int] = None
    Student_ID: Optional[int] = None
    Position: Optional[str] = None
    WeeklyHours: Optional[int] = None
    FultonFellow: Optional[str] = None
    Subject: Optional[str] = None
    CatalogNum: Optional[int] = None
    ClassSession: Optional[str] = None
    ClassNum: Optional[str] = None
    AcadCareer: Optional[str] = None
    # Add more fields as needed, e.g. Compensation, Position, etc.