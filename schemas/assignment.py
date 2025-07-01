from pydantic import BaseModel
from typing import Optional


class StudentClassAssignmentRead(BaseModel):
    Id: int
    Student_ID: int
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

    First_Name: Optional[str] = None
    Last_Name: Optional[str] = None
    Position_Number: Optional[str] = None
    I9_Sent: Optional[bool] = None
    SSN_Sent: Optional[bool] = None
    Offer_Sent: Optional[bool] = None
    Offer_Signed: Optional[bool] = None
    cum_gpa: Optional[float] = None
    cur_gpa: Optional[float] = None

    class Config:
        from_attributes = True
