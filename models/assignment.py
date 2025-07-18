from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from typing import ClassVar
from datetime import datetime, timezone

Base = declarative_base()


class StudentClassAssignment(Base):
    __tablename__: ClassVar[str] = 'StudentClassAssignments'
    __table_args__ = {'schema': 'dbo'}

    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    Student_ID = Column(Integer, nullable=False)
    ASUrite = Column(String, nullable=True)
    Position = Column(String, nullable=False)
    WeeklyHours = Column(Integer, nullable=False)
    FultonFellow = Column(String, nullable=False)
    Email = Column(String, nullable=False)
    EducationLevel = Column(String, nullable=False)
    Subject = Column(String, nullable=False)
    CatalogNum = Column(Integer, nullable=False)
    ClassSession = Column(String, nullable=False)
    ClassNum = Column(String, nullable=False)
    Term = Column(String, nullable=False)

    InstructorFirstName = Column(String, nullable=False)
    InstructorLastName = Column(String, nullable=False)
    InstructorID = Column(Integer, nullable=True)
    Instructor_Edit = Column(String(1), nullable=True)

    Compensation = Column(Float, nullable=False)
    CreatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    Location = Column(String(50), nullable=False)
    Campus = Column(String, nullable=False)
    AcadCareer = Column(String, nullable=False)
    CostCenterKey = Column(String, nullable=False)

    First_Name = Column(String, nullable=True)
    Last_Name = Column(String, nullable=True)
    Position_Number = Column(String, nullable=True)

    SSN_Sent = Column(Boolean, nullable=True)
    Offer_Sent = Column(Boolean, nullable=True)
    Offer_Signed = Column(Boolean, nullable=True)
    cum_gpa = Column(Float, nullable=True)
    cur_gpa = Column(Float, nullable=True)