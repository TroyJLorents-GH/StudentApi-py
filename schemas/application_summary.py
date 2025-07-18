from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicationSummaryDto(BaseModel):
    Id: int
    Email: str
    Name: str
    YourASUEmailAddress: str
    FirstName: str
    LastName: str
    ASU10DigitID: int
    DegreeProgram: str
    ExpectedGraduation: datetime
    GraduateGPA: str
    PositionsConsidered: Optional[str]
    PreferredCourses: Optional[str]
    TranscriptUrl: Optional[str]
    ResumeUrl: Optional[str]
    HoursAvailable: Optional[str]
    ProgrammingLanguage: Optional[str]
    TASpeakTestScoreOrIBT: Optional[str]
    DissertationProposalStatus: Optional[str]
    UndergraduateInstitution: str
    UndergraduateGPA: str

    class Config:
        orm_mode = True