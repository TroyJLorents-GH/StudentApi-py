from pydantic import BaseModel
from typing import Optional
from datetime import date


class PhdApplicationSummaryDto(BaseModel):
    Id: int
    Email: str
    Name: str
    ASUEmail: str
    FirstName: str
    LastName: str
    ASU_ID: int
    DegreeProgram: str
    ExpectedGraduation: date
    GraduateGPA: Optional[str]
    PositionsConsidered: Optional[str]
    PreferredCourses: Optional[str]
    TranscriptUrl: Optional[str]
    ResumeUrl: Optional[str]
    HoursAvailable: Optional[str]
    ProgrammingLanguages: str
    TASpeakTestScore: Optional[str]
    ThesisProposalStatus: Optional[str]
    ComprehensiveExam: Optional[str]
    ResearchAccomplishments: Optional[str]
    UndergraduateInstitution: str
    UndergraduateGPA: str
    StartOfPhdYear: Optional[str]

    class Config:
        from_attributes = True
