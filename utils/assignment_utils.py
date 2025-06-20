from models.assignment import StudentClassAssignment
from collections import namedtuple


def calculate_compensation(a):
    h = int(a.get("WeeklyHours", 0))
    position = a.get("Position")
    level = a.get("EducationLevel")
    fellow = a.get("FultonFellow")
    session = a.get("ClassSession")

    if position == "TA":
        if h == 10 and level == "MS" and fellow == "No":
            return 6636
        if h == 10 and level == "PHD" and fellow == "No":
            return 7250
        if h == 20 and level == "MS" and fellow == "No":
            return 13272
        if h == 20 and level == "PHD" and fellow == "No":
            return 14500
        if h == 20 and level == "PHD" and fellow == "Yes":
            return 13461.24

    if position == "TA (GSA) 1 credit":
        if h == 10 and level == "PHD" and fellow == "No":
            return 7552.5
        if h == 20 and level == "PHD" and fellow == "No":
            return 16825

    if position == "IA":
        base_factor = 2 if session == "C" else 1
        if level in ["MS", "PHD"]:
            return base_factor * 1100 * (h / 5)

    return 0


CostCenterRule = namedtuple("CostCenterRule", ["position", "location", "campus", "career", "key"])

COST_CENTER_RULES = [
    # === TA (GSA) 1 credit ===
    CostCenterRule("TA (GSA) 1 credit", "TEMPE", "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit", "TEMPE", "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit", "POLY", "POLY", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit", "POLY", "POLY", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "POLY", "GRAD", "------"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY", "GRAD", "------"),

    # === IA ===
    CostCenterRule("IA", "TEMPE", "TEMPE", "UGRD", "CC0136/PG15818"),
    CostCenterRule("IA", "TEMPE", "TEMPE", "GRAD", "CC0136/PG15818"),
    CostCenterRule("IA", "POLY", "POLY", "UGRD", "CC0136/PG15818"),
    CostCenterRule("IA", "POLY", "POLY", "GRAD", "CC0136/PG15818"),
    CostCenterRule("IA", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IA", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG01943"),
    CostCenterRule("IA", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("IA", "ASUONLINE", "POLY", "GRAD", "CC0136/PG02003"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG01943"),
    CostCenterRule("IA", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("IA", "ICOURSE", "POLY", "GRAD", "CC0136/PG02003"),

    # === Grader ===
    CostCenterRule("Grader", "TEMPE", "TEMPE", "UGRD", "CC0136/PG14700"),
    CostCenterRule("Grader", "TEMPE", "TEMPE", "GRAD", "CC0136/PG14700"),
    CostCenterRule("Grader", "POLY", "POLY", "UGRD", "CC0136/PG14700"),
    CostCenterRule("Grader", "POLY", "POLY", "GRAD", "CC0136/PG14700"),
    CostCenterRule("Grader", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("Grader", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("Grader", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("Grader", "ASUONLINE", "POLY", "GRAD", "------"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("Grader", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("Grader", "ICOURSE", "POLY", "GRAD", "------"),

    # === TA ===
    CostCenterRule("TA", "TEMPE", "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA", "TEMPE", "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA", "POLY", "POLY", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA", "POLY", "POLY", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA", "ASUONLINE", "POLY", "GRAD", "------"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA", "ICOURSE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA", "ICOURSE", "POLY", "GRAD", "------"),
]


def compute_cost_center_key(a):
    for rule in COST_CENTER_RULES:
        if (
            (rule.position or "").upper() == (a.get("Position") or "").upper()
            and (rule.location or "").upper() == (a.get("Location") or "").upper()
            and (rule.campus or "").upper() == (a.get("Campus") or "").upper()
            and (rule.career or "").upper() == (a.get("AcadCareer") or "").upper()
        ):
            return rule.key
    return "UNKNOWN"
