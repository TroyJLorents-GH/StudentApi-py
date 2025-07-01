from pydantic import BaseModel
from typing import Optional

class StudentClassAssignmentCreate(BaseModel):
    Student_ID: int
    Position: str
    Email: str
    First_Name: Optional[str] = None
    Last_Name: Optional[str] = None
    EducationLevel: str
    Subject: str
    CatalogNum: int
    ClassSession: str
    ClassNum: str
    Term: str
    InstructorFirstName: str
    InstructorLastName: str
    WeeklyHours: int
    FultonFellow: str
    Compensation: float
    Location: str
    Campus: str
    AcadCareer: str
    CostCenterKey: str
    cur_gpa: Optional[float] = None
    cum_gpa: Optional[float] = None
