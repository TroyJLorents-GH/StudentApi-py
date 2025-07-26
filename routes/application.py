from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.application import MastersIAGraderApplication2254
from schemas.application_summary import ApplicationSummaryDto


router = APIRouter(prefix="/api/MastersIAGraderApplication", tags=["MastersIAGraderApplication"])

@router.get("/", response_model=List[ApplicationSummaryDto])
def get_application_summaries(db: Session = Depends(get_db)):
    applications = db.query(MastersIAGraderApplication2254).all()

    return [
        ApplicationSummaryDto(
            Id=app.Id,
            Email=app.Email,
            Name=app.Name,
            YourASUEmailAddress=app.YourASUEmailAddress,
            FirstName=app.FirstName,
            LastName=app.LastName,
            ASU10DigitID=app.ASU10DigitID,
            DegreeProgram=app.DegreeProgram,
            ExpectedGraduation=app.ExpectedGraduation,
            GraduateGPA=app.GraduateGPA,
            PositionsConsidered=app.PositionsConsidered,
            PreferredCourses=app.PreferredCourses,
            TranscriptUrl=app.TranscriptUrl,
            ResumeUrl=app.ResumeUrl,
            HoursAvailable=app.HoursAvailable,
            ProgrammingLanguage=app.ProgrammingLanguages,
            TASpeakTestScoreOrIBT=app.TASpeakTestScoreOrIBT,
            DissertationProposalStatus=app.DissertationProposalStatus,
            UndergraduateInstitution=app.UndergraduateInstitution,
            UndergraduateGPA=app.UndergraduateGPA
        )
        for app in applications
    ]
