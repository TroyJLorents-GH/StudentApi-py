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
            return 8093.00
        if h == 20 and session in ["A", "B", "C"]:
            return 17600.00

    # --- TA (GSA) 1 credit + (PhD, Fulton Fellow: "No") ---
    if position == "TA (GSA) 1 credit +" and level == "PHD" and fellow == "No":
        if h == 10 and session in ["A", "B", "C"]:
            return 8800.00

    # --- TA ---
    if position == "TA":
        if h == 20 and level == "PHD" and fellow == "Yes" and session in ["A", "B", "C"]:
            return 13461.15
        if h == 10 and level == "PHD" and fellow == "Yes" and session in ["A", "B", "C"]:
            return 6730.58
        if h == 10 and level == "MS" and fellow == "No" and session in ["A", "B", "C"]:
            return 6636.00
        if h == 10 and level == "PHD" and fellow == "No" and session in ["A", "B", "C"]:
            return 7250.00
        if h == 20 and level == "MS" and fellow == "No" and session in ["A", "B", "C"]:
            return 13272.00
        if h == 20 and level == "PHD" and fellow == "No" and session in ["A", "B", "C"]:
            return 14500.00

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
    CostCenterRule("TA", "TEMPE",   "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA", "TEMPE",   "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),

    # IA
    CostCenterRule("IA", "TEMPE",   "TEMPE", "UGRD", "CC0136/PG15818"),
    CostCenterRule("IA", "TEMPE",   "TEMPE", "GRAD", "CC0136/PG15818"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IA", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG01943"),
    CostCenterRule("IA", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IA", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG01943"),

    # Grader
    CostCenterRule("Grader", "TEMPE",   "TEMPE", "UGRD", "CC0136/PG14700"),
    CostCenterRule("Grader", "TEMPE",   "TEMPE", "GRAD", "CC0136/PG14700"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("Grader", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("Grader", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("Grader", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("Grader", "WEST",   "TEMPE", "UGRD", "CC0136/PG14700"),

    # TA (GSA) 1 credit
    CostCenterRule("TA (GSA) 1 credit", "TEMPE",   "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit", "TEMPE",   "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),

    # TA (GSA) 1 credit +
    CostCenterRule("TA (GSA) 1 credit +", "TEMPE",   "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit +", "TEMPE",   "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),

    # IOR
    CostCenterRule("IOR", "TEMPE",   "TEMPE", "UGRD", "CC0136/PG02202"),
    CostCenterRule("IOR", "TEMPE",   "TEMPE", "GRAD", "CC0136/PG06875"),
    CostCenterRule("IOR", "ICOURSE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IOR", "ICOURSE", "TEMPE", "GRAD", "CC0136/PG06316"),
    CostCenterRule("IOR", "ASUONLINE", "TEMPE", "UGRD", "CC0136/PG01943"),
    CostCenterRule("IOR", "ASUONLINE", "TEMPE", "GRAD", "CC0136/PG06316"),

    # ===== POLY =====
    # TA
    CostCenterRule("TA", "POLY",    "POLY",  "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA", "POLY",    "POLY",  "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA", "ICOURSE", "POLY",  "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA", "ASUONLINE", "POLY",  "UGRD", "CC0136/PG02003"),

    # IA
    CostCenterRule("IA", "POLY",    "POLY",  "UGRD", "CC0136/PG15818"),
    CostCenterRule("IA", "POLY",    "POLY",  "GRAD", "CC0136/PG15818"),
    CostCenterRule("IA", "ICOURSE", "POLY",  "UGRD", "CC0136/PG02003"),
    CostCenterRule("IA", "ICOURSE", "POLY",  "GRAD", "CC0136/PG02003"),
    CostCenterRule("IA", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),
    CostCenterRule("IA", "ASUONLINE", "POLY", "GRAD", "CC0136/PG02003"),

    # Grader
    CostCenterRule("Grader", "POLY",    "POLY",  "UGRD", "CC0136/PG14700"),
    CostCenterRule("Grader", "POLY",    "POLY",  "GRAD", "CC0136/PG14700"),
    CostCenterRule("Grader", "ICOURSE", "POLY",  "UGRD", "CC0136/PG02003"),
    CostCenterRule("Grader", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),

    # TA (GSA) 1 credit
    CostCenterRule("TA (GSA) 1 credit", "POLY",    "POLY",  "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit", "POLY",    "POLY",  "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY",  "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),

    # TA (GSA) 1 credit +
    CostCenterRule("TA (GSA) 1 credit +", "POLY",    "POLY",  "UGRD", "CC0136/PG02202"),
    CostCenterRule("TA (GSA) 1 credit +", "POLY",    "POLY",  "GRAD", "CC0136/PG06875"),
    CostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "POLY",  "UGRD", "CC0136/PG02003"),
    CostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),

    # IOR
    CostCenterRule("IOR", "POLY",    "POLY",  "UGRD", "CC0136/PG02202"),
    CostCenterRule("IOR", "POLY",    "POLY",  "GRAD", "CC0136/PG06875"),
    CostCenterRule("IOR", "ICOURSE", "POLY",  "UGRD", "CC0136/PG02003"),
    CostCenterRule("IOR", "ASUONLINE", "POLY", "UGRD", "CC0136/PG02003"),

    # ===== WEST =====
    CostCenterRule("Grader", "WEST", "WEST", "UGRD", "CC0136/PG14700"),
]

# --- Summer Cost Center Rules (terms ending in 4) ---
SummerCostCenterRule = namedtuple("SummerCostCenterRule", ["position", "location", "campus", "key"])

SUMMER_COST_CENTER_RULES = [
    # ===== TEMPE =====
    SummerCostCenterRule("TA", "TEMPE", "TEMPE", "CC1139/PG08491 + DR07557"),
    SummerCostCenterRule("TA", "ASUONLINE", "TEMPE", "CC0136/PG01943"),
    SummerCostCenterRule("TA", "ICOURSE", "TEMPE", "CC0136/PG01943"),

    SummerCostCenterRule("IOR", "TEMPE", "TEMPE", "CC1139/PG08491 + DR07557"),
    SummerCostCenterRule("IOR", "ASUONLINE", "TEMPE", "CC0136/PG01943"),
    SummerCostCenterRule("IOR", "ICOURSE", "TEMPE", "CC0136/PG01943"),

    SummerCostCenterRule("IA", "TEMPE", "TEMPE", "CC1139/PG08491 + DR07557"),
    SummerCostCenterRule("IA", "ASUONLINE", "TEMPE", "CC0136/PG01943"),
    SummerCostCenterRule("IA", "ICOURSE", "TEMPE", "CC0136/PG01943"),

    SummerCostCenterRule("Grader", "TEMPE", "TEMPE", "CC1139/PG08491 + DR07557"),
    SummerCostCenterRule("Grader", "ASUONLINE", "TEMPE", "CC0136/PG01943"),
    SummerCostCenterRule("Grader", "ICOURSE", "TEMPE", "CC0136/PG01943"),

    SummerCostCenterRule("TA (GSA) 1 credit", "TEMPE", "TEMPE", "CC1139/PG08491 + DR07557"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "TEMPE", "CC0136/PG01943"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ICOURSE", "TEMPE", "CC0136/PG01943"),

    SummerCostCenterRule("TA (GSA) 1 credit +", "TEMPE", "TEMPE", "CC1139/PG08491 + DR07557"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "TEMPE", "CC0136/PG01943"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "TEMPE", "CC0136/PG01943"),

    # ===== POLY =====
    SummerCostCenterRule("TA", "POLY", "POLY", "CC1139/PG08524 + DR07557"),
    SummerCostCenterRule("TA", "ASUONLINE", "POLY", "CC0136/PG02003"),
    SummerCostCenterRule("TA", "ICOURSE", "POLY", "CC0136/PG02003"),

    SummerCostCenterRule("IOR", "POLY", "POLY", "CC1139/PG08524 + DR07557"),
    SummerCostCenterRule("IOR", "ASUONLINE", "POLY", "CC0136/PG02003"),
    SummerCostCenterRule("IOR", "ICOURSE", "POLY", "CC0136/PG02003"),

    SummerCostCenterRule("IA", "POLY", "POLY", "CC1139/PG08524 + DR07557"),
    SummerCostCenterRule("IA", "ASUONLINE", "POLY", "CC0136/PG02003"),
    SummerCostCenterRule("IA", "ICOURSE", "POLY", "CC0136/PG02003"),

    SummerCostCenterRule("Grader", "POLY", "POLY", "CC1139/PG08524 + DR07557"),
    SummerCostCenterRule("Grader", "ASUONLINE", "POLY", "CC0136/PG02003"),
    SummerCostCenterRule("Grader", "ICOURSE", "POLY", "CC0136/PG02003"),

    SummerCostCenterRule("TA (GSA) 1 credit", "POLY", "POLY", "CC1139/PG08524 + DR07557"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ASUONLINE", "POLY", "CC0136/PG02003"),
    SummerCostCenterRule("TA (GSA) 1 credit", "ICOURSE", "POLY", "CC0136/PG02003"),

    SummerCostCenterRule("TA (GSA) 1 credit +", "POLY", "POLY", "CC1139/PG08524 + DR07557"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ASUONLINE", "POLY", "CC0136/PG02003"),
    SummerCostCenterRule("TA (GSA) 1 credit +", "ICOURSE", "POLY", "CC0136/PG02003"),
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


RULES_VERSION = "2026-03-22"


def get_rules_version() -> str:
    """Return the current version of the compensation/cost center rules."""
    return RULES_VERSION
