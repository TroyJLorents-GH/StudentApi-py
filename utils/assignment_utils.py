from models.assignment import StudentClassAssignment
from collections import namedtuple

# --- Compensation Calculation ---


def calculate_compensation(a, term=None):
    h = int(a.get("WeeklyHours", 0))
    position = (a.get("Position") or "").strip()
    level = (a.get("EducationLevel") or "").strip().upper()
    fellow = (a.get("FultonFellow") or "").strip()
    session = (a.get("ClassSession") or "").strip().upper()

    # --- Grader ---
    if position == "Grader" and level in ["BS", "MS", "PHD"] and fellow == "No":
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

    # --- TA (GSA) 1 credit (PhD, Fulton Fellow: "No") ---
    if position == "TA (GSA) 1 credit" and level == "PHD" and fellow == "No":
        if h == 10 and session in ["A", "B", "C"]:
            return 8000.00
        if h == 20 and session in ["A", "B", "C"]:
            return 16000.00

    # --- TA (GSA) 1 credit + (PhD, Fulton Fellow: "No") ---
    if position == "TA (GSA) 1 credit +" and level == "PHD" and fellow == "No":
        if h == 10 and session in ["A", "B", "C"]:
            return 8500.00

    # --- TA ---
    if position == "TA":
        if h == 20 and level == "PHD" and fellow == "Yes" and session in ["A", "B", "C"]:
            return 13000.00
        if h == 10 and level == "PHD" and fellow == "Yes" and session in ["A", "B", "C"]:
            return 6500.00
        if h == 10 and level == "MS" and fellow == "No" and session in ["A", "B", "C"]:
            return 6000.00
        if h == 10 and level == "PHD" and fellow == "No" and session in ["A", "B", "C"]:
            return 7000.00
        if h == 20 and level == "MS" and fellow == "No" and session in ["A", "B", "C"]:
            return 12000.00
        if h == 20 and level == "PHD" and fellow == "No" and session in ["A", "B", "C"]:
            return 14000.00

    # --- IA (BS, MS or PHD, Fellow: No) ---
    if position == "IA" and level in ["BS", "MS", "PHD"] and fellow == "No":
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
    # ===== TEMPE =====
    # TA
    CostCenterRule("TA", "TEMPE",   "TEMPE", "UGRD", "CC9002/PG90003"),
    CostCenterRule("TA", "TEMPE",   "TEMPE", "GRAD", "CC9002/PG90004"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "GRAD", "CC9002/PG90006"),
    CostCenterRule("TA", "ASUONLINE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("TA", "ASUONLINE", "TEMPE", "GRAD", "CC9002/PG90006"),

    # IA
    CostCenterRule("IA", "TEMPE",   "TEMPE", "UGRD", "CC9002/PG90007"),
    CostCenterRule("IA", "TEMPE",   "TEMPE", "GRAD", "CC9002/PG90007"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "GRAD", "CC9002/PG90005"),
    CostCenterRule("IA", "ASUONLINE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("IA", "ASUONLINE", "TEMPE", "GRAD", "CC9002/PG90005"),

    # Grader
    CostCenterRule("Grader", "TEMPE",   "TEMPE", "UGRD", "CC9002/PG90008"),
    CostCenterRule("Grader", "TEMPE",   "TEMPE", "GRAD", "CC9002/PG90008"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "GRAD", "CC9002/PG90006"),
    CostCenterRule("Grader", "ASUONLINE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("Grader", "ASUONLINE", "TEMPE", "GRAD", "CC9002/PG90006"),
    CostCenterRule("Grader", "WEST",   "TEMPE", "UGRD", "CC9002/PG90008"),

    # TA (GSA) 1 credit
    CostCenterRule("TA (GSA) 1 credit", "TEMPE",   "TEMPE", "UGRD", "CC9002/PG90003"),
    CostCenterRule("TA (GSA) 1 credit", "TEMPE",   "TEMPE", "GRAD", "CC9002/PG90004"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "GRAD", "CC9002/PG90006"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "GRAD", "CC9002/PG90006"),

    # TA (GSA) 1 credit +
    CostCenterRule("TA (GSA) 1 credit +", "TEMPE",   "TEMPE", "UGRD", "CC9002/PG90003"),
    CostCenterRule("TA (GSA) 1 credit +", "TEMPE",   "TEMPE", "GRAD", "CC9002/PG90004"),
    CostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "TEMPE", "GRAD", "CC9002/PG90006"),
    CostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "TEMPE", "GRAD", "CC9002/PG90006"),

    # IOR
    CostCenterRule("IOR", "TEMPE",   "TEMPE", "UGRD", "CC9002/PG90003"),
    CostCenterRule("IOR", "TEMPE",   "TEMPE", "GRAD", "CC9002/PG90004"),
    CostCenterRule("IOR", "ICOURSE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("IOR", "ICOURSE", "TEMPE", "GRAD", "CC9002/PG90006"),
    CostCenterRule("IOR", "ASUONLINE", "TEMPE", "UGRD", "CC9002/PG90005"),
    CostCenterRule("IOR", "ASUONLINE", "TEMPE", "GRAD", "CC9002/PG90006"),

    # ===== POLY =====
    # TA
    CostCenterRule("TA", "POLY",    "POLY",  "UGRD", "CC9002/PG90003"),
    CostCenterRule("TA", "POLY",    "POLY",  "GRAD", "CC9002/PG90004"),
    CostCenterRule("TA", "ICOURSE", "POLY",  "UGRD", "CC9002/PG90009"),
    CostCenterRule("TA", "ASUONLINE", "POLY",  "UGRD", "CC9002/PG90009"),

    # IA
    CostCenterRule("IA", "POLY",    "POLY",  "UGRD", "CC9002/PG90007"),
    CostCenterRule("IA", "POLY",    "POLY",  "GRAD", "CC9002/PG90007"),
    CostCenterRule("IA", "ICOURSE", "POLY",  "UGRD", "CC9002/PG90009"),
    CostCenterRule("IA", "ICOURSE", "POLY",  "GRAD", "CC9002/PG90009"),
    CostCenterRule("IA", "ASUONLINE", "POLY", "UGRD", "CC9002/PG90009"),
    CostCenterRule("IA", "ASUONLINE", "POLY", "GRAD", "CC9002/PG90009"),

    # Grader
    CostCenterRule("Grader", "POLY",    "POLY",  "UGRD", "CC9002/PG90008"),
    CostCenterRule("Grader", "POLY",    "POLY",  "GRAD", "CC9002/PG90008"),
    CostCenterRule("Grader", "ICOURSE", "POLY",  "UGRD", "CC9002/PG90009"),
    CostCenterRule("Grader", "ASUONLINE", "POLY", "UGRD", "CC9002/PG90009"),

    # TA (GSA) 1 credit
    CostCenterRule("TA (GSA) 1 credit", "POLY",    "POLY",  "UGRD", "CC9002/PG90003"),
    CostCenterRule("TA (GSA) 1 credit", "POLY",    "POLY",  "GRAD", "CC9002/PG90004"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY",  "UGRD", "CC9002/PG90009"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "POLY", "UGRD", "CC9002/PG90009"),

    # TA (GSA) 1 credit +
    CostCenterRule("TA (GSA) 1 credit +", "POLY",    "POLY",  "UGRD", "CC9002/PG90003"),
    CostCenterRule("TA (GSA) 1 credit +", "POLY",    "POLY",  "GRAD", "CC9002/PG90004"),
    CostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "POLY",  "UGRD", "CC9002/PG90009"),
    CostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "POLY", "UGRD", "CC9002/PG90009"),

    # IOR
    CostCenterRule("IOR", "POLY",    "POLY",  "UGRD", "CC9002/PG90003"),
    CostCenterRule("IOR", "POLY",    "POLY",  "GRAD", "CC9002/PG90004"),
    CostCenterRule("IOR", "ICOURSE", "POLY",  "UGRD", "CC9002/PG90009"),
    CostCenterRule("IOR", "ASUONLINE", "POLY", "UGRD", "CC9002/PG90009"),

    # ===== WEST =====
    CostCenterRule("Grader", "WEST", "WEST", "UGRD", "CC9002/PG90008"),
]

# --- Summer Cost Center Rules (terms ending in 4) ---
SummerCostCenterRule = namedtuple("SummerCostCenterRule", ["position", "location", "campus", "key"])

SUMMER_COST_CENTER_RULES = [
    # ===== TEMPE =====
    SummerCostCenterRule("TA", "TEMPE", "TEMPE", "CC9001/PG90001 + DR00001"),
    SummerCostCenterRule("TA", "ASUONLINE", "TEMPE", "CC9002/PG90005"),
    SummerCostCenterRule("TA", "ICOURSE", "TEMPE", "CC9002/PG90005"),

    SummerCostCenterRule("IOR", "TEMPE", "TEMPE", "CC9001/PG90001 + DR00001"),
    SummerCostCenterRule("IOR", "ASUONLINE", "TEMPE", "CC9002/PG90005"),
    SummerCostCenterRule("IOR", "ICOURSE", "TEMPE", "CC9002/PG90005"),

    SummerCostCenterRule("IA", "TEMPE", "TEMPE", "CC9001/PG90001 + DR00001"),
    SummerCostCenterRule("IA", "ASUONLINE", "TEMPE", "CC9002/PG90005"),
    SummerCostCenterRule("IA", "ICOURSE", "TEMPE", "CC9002/PG90005"),

    SummerCostCenterRule("Grader", "TEMPE", "TEMPE", "CC9001/PG90001 + DR00001"),
    SummerCostCenterRule("Grader", "ASUONLINE", "TEMPE", "CC9002/PG90005"),
    SummerCostCenterRule("Grader", "ICOURSE", "TEMPE", "CC9002/PG90005"),

    SummerCostCenterRule("TA (GSA) 1 credit", "TEMPE", "TEMPE", "CC9001/PG90001 + DR00001"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "CC9002/PG90005"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "CC9002/PG90005"),

    SummerCostCenterRule("TA (GSA) 1 credit +", "TEMPE", "TEMPE", "CC9001/PG90001 + DR00001"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "TEMPE", "CC9002/PG90005"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "TEMPE", "CC9002/PG90005"),

    # ===== POLY =====
    SummerCostCenterRule("TA", "POLY", "POLY", "CC9001/PG90002 + DR00001"),
    SummerCostCenterRule("TA", "ASUONLINE", "POLY", "CC9002/PG90009"),
    SummerCostCenterRule("TA", "ICOURSE", "POLY", "CC9002/PG90009"),

    SummerCostCenterRule("IOR", "POLY", "POLY", "CC9001/PG90002 + DR00001"),
    SummerCostCenterRule("IOR", "ASUONLINE", "POLY", "CC9002/PG90009"),
    SummerCostCenterRule("IOR", "ICOURSE", "POLY", "CC9002/PG90009"),

    SummerCostCenterRule("IA", "POLY", "POLY", "CC9001/PG90002 + DR00001"),
    SummerCostCenterRule("IA", "ASUONLINE", "POLY", "CC9002/PG90009"),
    SummerCostCenterRule("IA", "ICOURSE", "POLY", "CC9002/PG90009"),

    SummerCostCenterRule("Grader", "POLY", "POLY", "CC9001/PG90002 + DR00001"),
    SummerCostCenterRule("Grader", "ASUONLINE", "POLY", "CC9002/PG90009"),
    SummerCostCenterRule("Grader", "ICOURSE", "POLY", "CC9002/PG90009"),

    SummerCostCenterRule("TA (GSA) 1 credit", "POLY", "POLY", "CC9001/PG90002 + DR00001"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "POLY", "CC9002/PG90009"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY", "CC9002/PG90009"),

    SummerCostCenterRule("TA (GSA) 1 credit +", "POLY", "POLY", "CC9001/PG90002 + DR00001"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "POLY", "CC9002/PG90009"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "POLY", "CC9002/PG90009"),
]


def compute_cost_center_key(a, term=None):
    position = (a.get("Position") or "").upper()
    location = (a.get("Location") or "").upper()
    campus = (a.get("Campus") or "").upper()
    career = (a.get("AcadCareer") or "").upper()

    # Summer terms (ending in 4) use simplified rules — career doesn't matter
    if term and str(term).endswith("4"):
        for rule in SUMMER_COST_CENTER_RULES:
            if (
                (rule.position or "").upper() == position and
                (rule.location or "").upper() == location and
                (rule.campus or "").upper() == campus
            ):
                return rule.key
        return "UNKNOWN"

    # Spring (1) / Fall (7) — career matters
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


RULES_VERSION = "2026-06-23"


def get_rules_version() -> str:
    """Return the current version of the compensation/cost center rules."""
    return RULES_VERSION

