from models.assignment import StudentClassAssignment
from collections import namedtuple

# --- Compensation Calculation ---


def calculate_compensation(a):
    h = int(a.get("WeeklyHours", 0))
    position = (a.get("Position") or "").strip()
    level = (a.get("EducationLevel") or "").strip().upper()
    fellow = (a.get("FultonFellow") or "").strip()
    session = (a.get("ClassSession") or "").strip().upper()

    # --- Grader ---
    if position == "Grader" and level in ["MS", "PHD"] and fellow == "No":
        if h == 5:
            if session in ["A", "B"]:
                return 781
            if session == "C":
                return 1562
        if h == 10:
            if session in ["A", "B"]:
                return 1562
            if session == "C":
                return 3124
        if h == 15:
            if session in ["A", "B"]:
                return 2343
            if session == "C":
                return 4686
        if h == 20:
            if session in ["A", "B"]:
                return 3124
            if session == "C":
                return 6248

    # --- TA (GSA) 1 credit ---
    if position == "TA (GSA) 1 credit" and level == "PHD" and fellow == "No":
        if h == 10 and session in ["A", "B", "C"]:
            return 7552.5
        if h == 20 and session in ["A", "B", "C"]:
            return 16825

    # --- TA ---
    if position == "TA":
        if h == 20 and level == "PHD" and fellow == "Yes" and session in ["A", "B", "C"]:
            return 13461.15
        if h == 10 and level == "MS" and fellow == "No" and session in ["A", "B", "C"]:
            return 6636
        if h == 10 and level == "PHD" and fellow == "No" and session in ["A", "B", "C"]:
            return 7250
        if h == 20 and level == "MS" and fellow == "No" and session in ["A", "B", "C"]:
            return 13272
        if h == 20 and level == "PHD" and fellow == "No" and session in ["A", "B", "C"]:
            return 14500

    # --- IA ---
    if position == "IA" and level in ["MS", "PHD"] and fellow == "No":
        if h == 5:
            if session in ["A", "B"]:
                return 1100
            if session == "C":
                return 2200
        if h == 10:
            if session in ["A", "B"]:
                return 2200
            if session == "C":
                return 4400
        if h == 15:
            if session in ["A", "B"]:
                return 2640
            if session == "C":
                return 6600
        if h == 20:
            if session in ["A", "B"]:
                return 4400
            if session == "C":
                return 8800

    return 0

# --- Cost Center Key ---

CostCenterRule = namedtuple("CostCenterRule", ["position", "location", "campus", "career", "key"])

COST_CENTER_RULES = [
    # TA (GSA) 1 credit
    CostCenterRule("TA (GSA) 1 credit", "TEMPE", "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit", "TEMPE", "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit", "POLY", "POLY", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit", "POLY", "POLY", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),

    # TA
    CostCenterRule("TA", "TEMPE", "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA", "TEMPE", "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA", "POLY", "POLY", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA", "POLY", "POLY", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),

    # IOR
    CostCenterRule("IOR", "TEMPE", "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("IOR", "TEMPE", "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("IOR", "POLY", "POLY", "UGRD", "CC0136/PG02202"),
    CostCenterRule("IOR", "POLY", "POLY", "GRAD", "CC0136/PG06875"),
    CostCenterRule("IOR", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IOR", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("IOR", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),

    # Grader
    CostCenterRule("Grader", "TEMPE", "TEMPE", "UGRD", "CC0136/PG14700"),
    CostCenterRule("Grader", "TEMPE", "TEMPE", "GRAD", "CC0136/PG14700"),
    CostCenterRule("Grader", "POLY", "POLY", "UGRD", "CC0136/PG14700"),
    CostCenterRule("Grader", "POLY", "POLY", "GRAD", "CC0136/PG14700"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("Grader", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),

    # IA
    CostCenterRule("IA", "TEMPE", "TEMPE", "UGRD", "CC0136/PG15818"),
    CostCenterRule("IA", "TEMPE", "TEMPE", "GRAD", "CC0136/PG15818"),
    CostCenterRule("IA", "POLY", "POLY", "UGRD", "CC0136/PG15818"),
    CostCenterRule("IA", "POLY", "POLY", "GRAD", "CC0136/PG15818"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG01943"),
    CostCenterRule("IA", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("IA", "ICOURSE", "POLY", "GRAD", "CC0136/PG02003"),
]


def compute_cost_center_key(a):
    position = (a.get("Position") or "").upper()
    location = (a.get("Location") or "").upper()
    campus = (a.get("Campus") or "").upper()
    career = (a.get("AcadCareer") or "").upper()
    for rule in COST_CENTER_RULES:
        if (
            (rule.position or "").upper() == position and
            (rule.location or "").upper() == location and
            (rule.campus or "").upper() == campus and
            (rule.career or "").upper() == career
        ):
            return rule.key
    return "UNKNOWN"


# --- Helper: Infer AcadCareer from CatalogNum ---


def infer_acad_career(row):
    try:
        num = int(row.get("CatalogNum", 0))
    except Exception:
        return "UGRD"
    return "UGRD" if 100 <= num <= 499 else "GRAD"