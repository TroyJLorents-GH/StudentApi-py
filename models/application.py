from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class MastersIAGraderApplication2254(Base):
    __tablename__ = "MastersIAGraderApplication2254"
    __table_args__ = {"schema": "dbo"}

    Id = Column(Integer, primary_key=True, index=True)
    Start_time = Column(DateTime, nullable=True)
    Completion_time = Column(DateTime, nullable=True)

    Email = Column(String(50), nullable=False)
    Name = Column(String(50), nullable=False)
    YourASUEmailAddress = Column("Your_ASU_Email_address", String(50), nullable=False)
    FirstName = Column("First_Name", String(50), nullable=False)
    LastName = Column("Last_Name", String(50), nullable=False)
    ASU10DigitID = Column("ASU_10_digit_ID", Integer, nullable=False)
    DegreeProgram = Column("Degree_Program_you_are_enrolled_in", String(100), nullable=False)

    CulminatingExperienceOption = Column("For_M_S_students_choose_culminating_experience_option", String(500))
    FacultyAdvisor = Column("Faculty_Thesis_Dissertation_Advisor_if_applicable_for_thesis", String(100))
    TASpeakTestScoreOrIBT = Column("TA_Speak_Test_Score_or_iBT", String(100))
    ExperienceSummary = Column("Experience_Summary", String)
    ProgrammingLanguages = Column("What_programming_languages_are_you_familiar_with", String, nullable=False)
    SpeakTestRemediation = Column("If_you_did_not_pass_the_TA_Speak_Test_are_you_attending", String(50))
    DissertationProposalStatus = Column("For_MS_Thesis_students_Did_you_complete_your_Dissertation_Thesis_Proposal",
                                        String(50))
    UndergraduateInstitution = Column("Your_undergraduate_Institution_University_of_your_bachelors_degree", String(500),
                                      nullable=False)
    UndergraduateGPA = Column("Cumulative_undergraduate_GPA", String(250), nullable=False)
    FirstSemesterGrad = Column("First_Semester_enrolled_grad_program", String(350), nullable=False)
    GraduateGPA = Column("GPA_of_graduate_courses_completed_so_far_at_ASU_type_NONE_if_no_GPA_earned_yet_at_ASU",
                         String(500), nullable=False)
    ExpectedGraduation = Column("Expected_graduation_semester_month_year_in_mm_yyyy_format", DateTime, nullable=False)
    PositionsConsidered = Column("Which_positions_would_you_like_to_be_considered_for_Select_all_that_apply", String)
    HoursAvailable = Column("How_many_hours_per_week_would_you_be_available_to_work", String(250))
    PreferredCourses = Column("Provide_preferred_courses_that_you_would_like_to_be_be_considered_for_if_any",
                              String(2500))
    TranscriptUrl = Column("Please_upload_your_ASU_transcript_in_pdf_format", String)
    ResumeUrl = Column("Provide_a_web_link_pointing_to_a_copy_of_your_Resume_E_g_LinkedIn_or_cloud_location", String)
    IAgree = Column("I_agree", String(50), nullable=False)
