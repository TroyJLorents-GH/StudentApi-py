from sqlalchemy import Column, String, Integer
from database import Base


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
