import os
from sqlalchemy import Column, String, Integer, Date
from database import Base


# Single stacked schedule table (renamed from ClassSchedule2261). Default term
# is the one whose rows live in the replica's Azure DB.
ACTIVE_TERM = os.getenv("ACTIVE_TERM", "2261")


class ClassSchedule(Base):
    __tablename__ = "ClassSchedule"
    __table_args__ = {"schema": "dbo"}

    ClassNum = Column(String, primary_key=True, index=True)
    Term = Column(String, nullable=True)
    Session = Column(String, nullable=False)
    Subject = Column(String, nullable=False)
    CatalogNum = Column(Integer, nullable=False)
    SectionNum = Column(Integer, nullable=False)
    Title = Column(String, nullable=False)
    InstructorID = Column(Integer, nullable=True)
    InstructorLastName = Column(String, nullable=False)
    InstructorFirstName = Column(String, nullable=False)
    InstructorEmail = Column(String, nullable=False)
    Location = Column(String, nullable=False)
    Campus = Column(String, nullable=False)
    AcadCareer = Column(String, nullable=False)

    # --- Newly added fields ---
    Component = Column(String(50), nullable=True)
    # Replica's real column is "InstructorMode"; source code refers to it as InstructMode.
    InstructMode = Column("InstructorMode", String(50), nullable=True)
    EndDate = Column(Date, nullable=True)
    EnrollCap = Column(Integer, nullable=True)
    EnrollTotal = Column(Integer, nullable=True)

    # --- Analytics columns ---
    # ClassType 'E' = enrollment section (LEC); 'N' = mirrored REC/LAB component
    # (must NOT be double-counted). ClassStatus 'A' = active, 'X' = cancelled.
    ClassType = Column(String(5), nullable=True)
    ClassStatus = Column(String(5), nullable=True)
    AssocClassNum = Column(Integer, nullable=True)
