from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models.phd_application import PhdApplication, ACTIVE_TERM
from schemas.phd_application_summary import PhdApplicationSummaryDto

router = APIRouter(prefix="/api/PhdApplication", tags=["PhdApplication"])


@router.get("", response_model=List[PhdApplicationSummaryDto])
@router.get("/", response_model=List[PhdApplicationSummaryDto])
def get_phd_application_summaries(term: Optional[str] = Query(None), db: Session = Depends(get_db)):
    use_term = term if term else ACTIVE_TERM
    applications = db.query(PhdApplication)\
        .filter(PhdApplication.TermCode == use_term)\
        .all()

    return [
        PhdApplicationSummaryDto(
            Id=app.Id,
            Email=app.Email,
            Name=app.Name,
            ASUEmail=app.ASUEmail,
            FirstName=app.FirstName,
            LastName=app.LastName,
            ASU_ID=app.ASU_ID,
            DegreeProgram=app.DegreeProgram,
            ExpectedGraduation=app.ExpectedGraduation,
            GraduateGPA=app.GraduateGPA,
            PositionsConsidered=app.PositionsConsidered,
            PreferredCourses=app.PreferredCourses,
            TranscriptUrl=app.TranscriptUrl,
            ResumeUrl=app.ResumeUrl,
            HoursAvailable=app.HoursAvailable,
            ProgrammingLanguages=app.ProgrammingLanguages,
            TASpeakTestScore=app.TASpeakTestScore,
            ThesisProposalStatus=app.DissertationProposalStatus,
            ComprehensiveExam=app.ComprehensiveExam,
            ResearchAccomplishments=app.ResearchAccomplishments,
            UndergraduateInstitution=app.UndergraduateInstitution,
            UndergraduateGPA=app.UndergraduateGPA,
            StartOfPhdYear=app.StartOfPhdYear
        )
        for app in applications
    ]
