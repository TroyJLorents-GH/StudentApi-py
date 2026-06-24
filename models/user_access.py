from sqlalchemy import Column, String, Boolean
from database import Base


class UserAccess(Base):
    __tablename__ = "user_access"
    __table_args__ = {'schema': 'dbo'}

    asu_id = Column(String(50), primary_key=True, index=True)
    role = Column(String(20), nullable=False)

    name = Column(String(100), nullable=True)
    emplid = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    position_title = Column(String(100), nullable=True)
    program = Column(String(50), nullable=True)

    faculty_dashboard = Column(Boolean, default=False, nullable=False)
    assignment_adder = Column(Boolean, default=False, nullable=False)
    applications = Column(Boolean, default=False, nullable=False)
    phd_applications = Column(Boolean, default=False, nullable=False)
    student_summary_page = Column(Boolean, default=False, nullable=False)
    bulk_upload_assignments = Column(Boolean, default=False, nullable=False)
    manage_assignments = Column(Boolean, default=False, nullable=False)
    login = Column(Boolean, default=False, nullable=False)
    master_dashboard = Column(Boolean, default=False, nullable=False)
    program_chair_uploads = Column(Boolean, default=False, nullable=False)
    faculty_quickassign = Column(Boolean, default=False, nullable=False)
    faculty_grader_uploads = Column(Boolean, default=False, nullable=False)
    analytics = Column(Boolean, default=False, nullable=False)
    chat = Column(Boolean, default=False, nullable=False)
