from pydantic import BaseModel
from typing import Optional

from datetime import datetime, timezone


class StudentClassAssignmentRead(BaseModel):
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
    Compensation: float
    Location: str
    Campus: str
    AcadCareer: str
    CostCenterKey: str
    CreatedAt: Optional[datetime] = None
    Instructor_Edit: Optional[str] = None

    First_Name: Optional[str] = None
    Last_Name: Optional[str] = None
    Position_Number: Optional[str] = None
    SSN_Sent: Optional[bool] = None
    Offer_Sent: Optional[bool] = None
    Offer_Signed: Optional[bool] = None
    cum_gpa: Optional[float] = None
    cur_gpa: Optional[float] = None


    class Config:
        from_attributes = True