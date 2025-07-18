from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StudentLookup(Base):
    __tablename__ = 'StudentData'
    __table_args__ = {'schema': 'dbo'}

    Student_ID = Column(Integer, primary_key=True, index=True)

    Cumulative_GPA = Column(Float, nullable=False)
    Current_GPA = Column(Float, nullable=False)

    Term_Code = Column(Integer, nullable=True)
    Admit_Term = Column(Integer, nullable=True)

    ASUrite = Column(String(50), nullable=False)
    First_Name = Column(String(75), nullable=False)
    Last_Name = Column(String(100), nullable=False)
    Middle_Name = Column(String(75), nullable=True)
    Preferred_Primary_First_Name = Column(String(75), nullable=True)

    ASU_Email_Adress = Column(String(150), nullable=False)

    Acad_Prog = Column(String(20), nullable=False)
    Acad_Prog_Descr = Column(String(150), nullable=False)
    Acad_Career = Column(String(10), nullable=False)
    Acad_Group = Column(String(10), nullable=False)
    Acad_Org = Column(String(25), nullable=False)
    Acad_Plan = Column(String(50), nullable=False)
    Plan_Descr = Column(String(100), nullable=False)
    Degree = Column(String(25), nullable=False)
    Transcript_Description = Column(String(200), nullable=False)
    Plan_Type = Column(String(50), nullable=False)
    Acad_Lvl_BOT = Column(String(50), nullable=False)
    Acad_Lvl_EOT = Column(String(50), nullable=False)
    Prog_Status = Column(String(50), nullable=False)

    Expected_Graduation_Term = Column(String(50), nullable=True)
    Campus = Column(String(50), nullable=False)
    Deans_List = Column(String(50), nullable=False)