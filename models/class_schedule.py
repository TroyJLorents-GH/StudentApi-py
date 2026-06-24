import os
from sqlalchemy import Column, String, Integer, Date
from database import Base


ACTIVE_TERM = os.getenv("ACTIVE_TERM", "2264")


class ClassSchedule2254(Base):
    __tablename__ = "ClassSchedule2254"
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
    InstructMode = Column(String(50), nullable=True)
    EndDate = Column(Date, nullable=True)
    EnrollCap = Column(Integer, nullable=True)
    EnrollTotal = Column(Integer, nullable=True)

    # --- Analytics columns ---
    ClassType = Column(String(5), nullable=True)
    ClassStatus = Column(String(5), nullable=True)
    AssocClassNum = Column(Integer, nullable=True)


class ClassSchedule2261(Base):
    __tablename__ = "ClassSchedule2261"
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
    InstructMode = Column(String(50), nullable=True)
    EndDate = Column(Date, nullable=True)
    EnrollCap = Column(Integer, nullable=True)
    EnrollTotal = Column(Integer, nullable=True)

    # --- Analytics columns ---
    ClassType = Column(String(5), nullable=True)
    ClassStatus = Column(String(5), nullable=True)
    AssocClassNum = Column(Integer, nullable=True)


class ClassSchedule2264(Base):
    __tablename__ = "ClassSchedule2264"
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
    InstructMode = Column(String(50), nullable=True)
    EndDate = Column(Date, nullable=True)
    EnrollCap = Column(Integer, nullable=True)
    EnrollTotal = Column(Integer, nullable=True)

    # --- Analytics columns ---
    ClassType = Column(String(5), nullable=True)
    ClassStatus = Column(String(5), nullable=True)
    AssocClassNum = Column(Integer, nullable=True)
