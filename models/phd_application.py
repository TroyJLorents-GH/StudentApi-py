import os
from sqlalchemy import Column, Integer, String, DateTime, Date
from database import Base

ACTIVE_TERM = os.getenv("ACTIVE_TERM", "2254")


class PhdApplication(Base):
    __tablename__ = "PhdApplication"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True)
    TermCode = Column(String(4), primary_key=True)
    StartTime = Column(DateTime, nullable=True)
    CompletionTime = Column(DateTime, nullable=True)

    ASU_ID = Column(Integer, nullable=False)
    Email = Column(String(50), nullable=False)
    Name = Column(String(50), nullable=False)
    ASUEmail = Column(String(50), nullable=False)
    FirstName = Column(String(50), nullable=False)
    LastName = Column(String(50), nullable=False)
    DegreeProgram = Column(String(150), nullable=False)

    FacultyAdvisor = Column(String(150))
    TASpeakTestScore = Column(String(150))
    SpeakTestRemediation = Column(String(50))
    ExperienceSummary = Column(String)
    ProgrammingLanguages = Column(String, nullable=False)
    DissertationProposalStatus = Column(String(50))
    ComprehensiveExam = Column(String(50))
    ResearchAccomplishments = Column(String)
    UndergraduateInstitution = Column(String(150), nullable=False)
    UndergraduateGPA = Column(String(50), nullable=False)
    FirstSemesterGrad = Column(String(350), nullable=False)
    GraduateGPA = Column(String(500))
    ExpectedGraduation = Column(Date, nullable=False)
    PositionsConsidered = Column(String)
    HoursAvailable = Column(String(250))
    StartOfPhdYear = Column(String(255), nullable=True)
    PreferredCourses = Column(String)
    TranscriptUrl = Column(String)
    ResumeUrl = Column(String)
    IAgree = Column(String(50), nullable=False)
