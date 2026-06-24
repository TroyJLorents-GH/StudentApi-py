from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, not_, and_
from typing import Optional

from models.assignment import StudentClassAssignment
from models.class_schedule import ClassSchedule, ACTIVE_TERM
from models.student import StudentLookup
from database import get_db
from dependencies import require_perm

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# Truly-hired filter: Instructor_Edit is null/''/'N' (not edited 'Y' or deleted 'D').
# Same rule as the Master Dashboard main tab.
def _hired_filter():
    return or_(
        StudentClassAssignment.Instructor_Edit == None,  # noqa: E711
        not_(StudentClassAssignment.Instructor_Edit.in_(["Y", "D"])),
    )


def _enroll_sections():
    """Count enrollment only from active enrollment sections: ClassType 'E'
    (the LEC where students enroll) and ClassStatus 'A' (offered). Excludes the
    'N' components (REC/LAB) that mirror the lecture — summing them double-counts."""
    return and_(ClassSchedule.ClassType == "E", ClassSchedule.ClassStatus == "A")


def _normalized(categories, series):
    """series: list of (label, list-of-numbers). Returns the standard chart payload."""
    return {
        "categories": list(categories),
        "series": [{"label": lbl, "data": [float(x) for x in data]} for lbl, data in series],
    }


@router.get("/trend")
def get_hiring_trend(
    groupBy: str = Query("class", pattern="^(class|instructor)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: dict = Depends(require_perm("analytics")),
):
    """
    Cross-term hire counts for the trend chart.
    Returns { terms: [...], series: [{ key, counts: [...] }] } where counts
    align with the terms array. Top-N keys by total hires across all terms.
    """
    # Group by raw columns and build the display key in Python — SQL Server
    # rejects GROUP BY on CONCAT(...) with bound parameters (error 8120).
    if groupBy == "instructor":
        key_cols = [
            StudentClassAssignment.InstructorFirstName,
            StudentClassAssignment.InstructorLastName,
        ]
    else:
        key_cols = [
            StudentClassAssignment.Subject,
            StudentClassAssignment.CatalogNum,
        ]

    raw = (
        db.query(
            StudentClassAssignment.Term.label("term"),
            *key_cols,
            func.count().label("hires"),
        )
        .filter(_hired_filter())
        .group_by(StudentClassAssignment.Term, *key_cols)
        .all()
    )

    class Row:  # lightweight: (term, key, hires)
        __slots__ = ("term", "key", "hires")

        def __init__(self, term, key, hires):
            self.term, self.key, self.hires = term, key, hires

    rows = [Row(r[0], f"{r[1]} {r[2]}".strip(), r[3]) for r in raw]

    terms = sorted({r.term for r in rows})

    # Total hires per key across all terms -> pick top N
    totals = {}
    for r in rows:
        totals[r.key] = totals.get(r.key, 0) + r.hires
    top_keys = sorted(totals, key=totals.get, reverse=True)[:limit]

    counts_map = {(r.term, r.key): r.hires for r in rows}
    series = [
        {
            "key": k,
            "total": totals[k],
            "counts": [counts_map.get((t, k), 0) for t in terms],
        }
        for k in top_keys
    ]

    return {"terms": terms, "series": series}


@router.get("/enrollment")
def get_enrollment_heatmap(
    term: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_perm("analytics")),
):
    """
    Per-class enrollment (one row per ClassNum) for the heatmap and bars.
    Aggregation by course/subject happens client-side.
    """
    use_term = term if term else ACTIVE_TERM

    rows = (
        db.query(
            ClassSchedule.ClassNum.label("classNum"),
            ClassSchedule.Subject.label("subject"),
            ClassSchedule.CatalogNum.label("catalogNum"),
            ClassSchedule.EnrollTotal.label("enrollTotal"),
            ClassSchedule.EnrollCap.label("enrollCap"),
        )
        .filter(ClassSchedule.Term == use_term, _enroll_sections())
        .all()
    )

    return [
        {
            "classNum": r.classNum,
            "subject": r.subject,
            "catalogNum": r.catalogNum,
            "enrollTotal": int(r.enrollTotal or 0),
            "enrollCap": int(r.enrollCap or 0),
        }
        for r in rows
    ]


@router.get("/hiring/by-term")
def hiring_by_term(db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    rows = (
        db.query(
            StudentClassAssignment.Term.label("term"),
            StudentClassAssignment.Position.label("position"),
            func.count().label("n"),
        )
        .filter(_hired_filter())
        .group_by(StudentClassAssignment.Term, StudentClassAssignment.Position)
        .all()
    )
    terms = sorted({r.term for r in rows})
    positions = sorted({r.position or "Unknown" for r in rows})
    cell = {(r.term, r.position or "Unknown"): r.n for r in rows}
    series = [(p, [cell.get((t, p), 0) for t in terms]) for p in positions]
    return _normalized(terms, series)


@router.get("/hiring/compensation-by-term")
def hiring_comp_by_term(db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    rows = (
        db.query(StudentClassAssignment.Term.label("term"), func.sum(StudentClassAssignment.Compensation).label("total"))
        .filter(_hired_filter())
        .group_by(StudentClassAssignment.Term)
        .all()
    )
    rows = sorted(rows, key=lambda r: r.term)
    return _normalized([r.term for r in rows], [("Total compensation", [r.total or 0 for r in rows])])


@router.get("/hiring/by-position")
def hiring_by_position(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                       user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    rows = (
        db.query(StudentClassAssignment.Position.label("position"), func.count().label("n"))
        .filter(_hired_filter(), StudentClassAssignment.Term == use_term)
        .group_by(StudentClassAssignment.Position)
        .all()
    )
    rows = sorted(rows, key=lambda r: r.position or "")
    return _normalized([r.position or "Unknown" for r in rows], [("Hires", [r.n for r in rows])])


@router.get("/hiring/top-instructors")
def hiring_top_instructors(term: Optional[str] = Query(None), limit: int = Query(10, ge=1, le=50),
                           db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    rows = (
        db.query(
            StudentClassAssignment.InstructorFirstName.label("fn"),
            StudentClassAssignment.InstructorLastName.label("ln"),
            func.count().label("n"),
        )
        .filter(_hired_filter(), StudentClassAssignment.Term == use_term)
        .group_by(StudentClassAssignment.InstructorFirstName, StudentClassAssignment.InstructorLastName)
        .all()
    )
    ranked = sorted(rows, key=lambda r: r.n, reverse=True)[:limit]
    labels = [f"{r.fn or ''} {r.ln or ''}".strip() or "Unknown" for r in ranked]
    return _normalized(labels, [("Hires", [r.n for r in ranked])])


@router.get("/hiring/kpis")
def hiring_kpis(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    q = db.query(StudentClassAssignment).filter(_hired_filter(), StudentClassAssignment.Term == use_term)
    hires = q.count()
    total_hours = db.query(func.coalesce(func.sum(StudentClassAssignment.WeeklyHours), 0)).filter(
        _hired_filter(), StudentClassAssignment.Term == use_term).scalar()
    total_comp = db.query(func.coalesce(func.sum(StudentClassAssignment.Compensation), 0)).filter(
        _hired_filter(), StudentClassAssignment.Term == use_term).scalar()
    instructors = db.query(StudentClassAssignment.InstructorLastName).filter(
        _hired_filter(), StudentClassAssignment.Term == use_term).distinct().count()
    return {"hires": hires, "weeklyHours": int(total_hours or 0),
            "compensation": float(total_comp or 0), "instructors": instructors}


@router.get("/enrollment/by-subject")
def enrollment_by_subject(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                          user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    rows = (
        db.query(ClassSchedule.Subject.label("subject"),
                 func.sum(ClassSchedule.EnrollTotal).label("total"))
        .filter(ClassSchedule.Term == use_term, _enroll_sections())
        .group_by(ClassSchedule.Subject).all()
    )
    rows = sorted(rows, key=lambda r: r.subject or "")
    return _normalized([r.subject for r in rows], [("Enrollment", [r.total or 0 for r in rows])])


@router.get("/enrollment/fill-rate-by-subject")
def enrollment_fill_rate(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                         user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    rows = (
        db.query(ClassSchedule.Subject.label("subject"),
                 func.sum(ClassSchedule.EnrollTotal).label("tot"),
                 func.sum(ClassSchedule.EnrollCap).label("cap"))
        .filter(ClassSchedule.Term == use_term, _enroll_sections())
        .group_by(ClassSchedule.Subject).all()
    )
    rows = sorted(rows, key=lambda r: r.subject or "")
    pct = [round(100.0 * (r.tot or 0) / r.cap, 1) if r.cap else 0 for r in rows]
    return _normalized([r.subject for r in rows], [("Fill rate %", pct)])


@router.get("/enrollment/top-instructors")
def enrollment_top_instructors(term: Optional[str] = Query(None), limit: int = Query(10, ge=1, le=50),
                               db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    rows = (
        db.query(ClassSchedule.InstructorFirstName.label("fn"), ClassSchedule.InstructorLastName.label("ln"),
                 func.sum(ClassSchedule.EnrollTotal).label("tot"))
        .filter(ClassSchedule.Term == use_term, _enroll_sections())
        .group_by(ClassSchedule.InstructorFirstName, ClassSchedule.InstructorLastName).all()
    )
    ranked = sorted(rows, key=lambda r: r.tot or 0, reverse=True)[:limit]
    labels = [f"{r.fn or ''} {r.ln or ''}".strip() or "Unknown" for r in ranked]
    return _normalized(labels, [("Enrollment", [r.tot or 0 for r in ranked])])


@router.get("/enrollment/mode-mix")
def enrollment_mode_mix(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                        user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    rows = (
        db.query(ClassSchedule.InstructMode.label("mode"), func.count().label("n"))
        .filter(ClassSchedule.Term == use_term, _enroll_sections())
        .group_by(ClassSchedule.InstructMode).all()
    )
    rows = sorted(rows, key=lambda r: r.mode or "")
    return _normalized([r.mode or "Unknown" for r in rows], [("Sections", [r.n for r in rows])])


@router.get("/enrollment/kpis")
def enrollment_kpis(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                    user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    base = db.query(ClassSchedule).filter(ClassSchedule.Term == use_term, _enroll_sections())
    sections = base.count()
    tot = db.query(func.coalesce(func.sum(ClassSchedule.EnrollTotal), 0)).filter(ClassSchedule.Term == use_term, _enroll_sections()).scalar()
    cap = db.query(func.coalesce(func.sum(ClassSchedule.EnrollCap), 0)).filter(ClassSchedule.Term == use_term, _enroll_sections()).scalar()
    instructors = db.query(ClassSchedule.InstructorLastName).filter(ClassSchedule.Term == use_term, _enroll_sections()).distinct().count()
    fill = round(100.0 * (tot or 0) / cap, 1) if cap else 0
    return {"enrollment": int(tot or 0), "sections": sections, "fillRate": fill, "instructors": instructors}


def _student_term_filter(q, term):
    if term:
        try:
            return q.filter(StudentLookup.Term_Code == int(term))
        except (TypeError, ValueError):
            return q
    return q


@router.get("/students/by-degree")
def students_by_degree(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                       user: dict = Depends(require_perm("analytics"))):
    q = db.query(StudentLookup.Degree.label("degree"), func.count().label("n")).group_by(StudentLookup.Degree)
    rows = _student_term_filter(q, term).all()
    rows = sorted(rows, key=lambda r: r.degree or "")
    return _normalized([r.degree or "Unknown" for r in rows], [("Students", [r.n for r in rows])])


@router.get("/students/by-org")
def students_by_org(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                    user: dict = Depends(require_perm("analytics"))):
    q = db.query(StudentLookup.Acad_Org.label("org"), func.count().label("n")).group_by(StudentLookup.Acad_Org)
    rows = _student_term_filter(q, term).all()
    rows = sorted(rows, key=lambda r: (r.n or 0), reverse=True)
    return _normalized([r.org or "Unknown" for r in rows], [("Students", [r.n for r in rows])])


@router.get("/students/by-plan")
def students_by_plan(degree: str = Query("PHD"), term: Optional[str] = Query(None),
                     limit: int = Query(20, ge=1, le=100),
                     db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    """Students grouped by Plan_Descr for a given degree level (PHD/MS/BS). Top-N plans."""
    q = (db.query(StudentLookup.Plan_Descr.label("plan"), func.count().label("n"))
         .filter(StudentLookup.Degree.ilike(f"%{degree}%"))
         .group_by(StudentLookup.Plan_Descr))
    rows = _student_term_filter(q, term).all()
    ranked = sorted(rows, key=lambda r: r.n or 0, reverse=True)[:limit]
    return _normalized([r.plan or "Unknown" for r in ranked], [(f"{degree} students", [r.n for r in ranked])])


@router.get("/students/by-campus")
def students_by_campus(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                       user: dict = Depends(require_perm("analytics"))):
    q = db.query(StudentLookup.Campus.label("campus"), func.count().label("n")).group_by(StudentLookup.Campus)
    rows = _student_term_filter(q, term).all()
    rows = sorted(rows, key=lambda r: (r.n or 0), reverse=True)
    return _normalized([r.campus or "Unknown" for r in rows], [("Students", [r.n for r in rows])])


@router.get("/students/kpis")
def students_kpis(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                  user: dict = Depends(require_perm("analytics"))):
    base = _student_term_filter(db.query(StudentLookup), term)
    total = base.count()
    def deg(p):
        return _student_term_filter(db.query(StudentLookup).filter(StudentLookup.Degree.ilike(p)), term).count()
    return {"total": total, "phd": deg("%PHD%"), "ms": deg("%MS%"), "bs": deg("%BS%")}


@router.get("/cross/grader-ratio-by-subject")
def grader_ratio_by_subject(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                            user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    enr = dict(
        db.query(ClassSchedule.Subject, func.sum(ClassSchedule.EnrollTotal))
        .filter(ClassSchedule.Term == use_term, _enroll_sections()).group_by(ClassSchedule.Subject).all()
    )
    grad = dict(
        db.query(StudentClassAssignment.Subject, func.count())
        .filter(_hired_filter(), StudentClassAssignment.Term == use_term,
                StudentClassAssignment.Position == "Grader")
        .group_by(StudentClassAssignment.Subject).all()
    )
    subjects = sorted(set(enr) | set(grad))
    return _normalized(subjects, [
        ("Enrollment", [enr.get(s, 0) or 0 for s in subjects]),
        ("Graders", [grad.get(s, 0) or 0 for s in subjects]),
    ])


@router.get("/cross/cost-per-enrolled-by-subject")
def cost_per_enrolled(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                      user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    comp = dict(
        db.query(StudentClassAssignment.Subject, func.sum(StudentClassAssignment.Compensation))
        .filter(_hired_filter(), StudentClassAssignment.Term == use_term)
        .group_by(StudentClassAssignment.Subject).all()
    )
    enr = dict(
        db.query(ClassSchedule.Subject, func.sum(ClassSchedule.EnrollTotal))
        .filter(ClassSchedule.Term == use_term, _enroll_sections()).group_by(ClassSchedule.Subject).all()
    )
    subjects = sorted(set(comp) & set(enr))
    data = [round((comp.get(s, 0) or 0) / e, 2) if (e := enr.get(s, 0)) else 0 for s in subjects]
    return _normalized(subjects, [("Cost per enrolled ($)", data)])


@router.get("/cross/offer-pipeline")
def offer_pipeline(term: Optional[str] = Query(None), db: Session = Depends(get_db),
                   user: dict = Depends(require_perm("analytics"))):
    use_term = term or ACTIVE_TERM
    base = db.query(StudentClassAssignment).filter(_hired_filter(), StudentClassAssignment.Term == use_term)
    hired = base.count()
    offer_sent = base.filter(StudentClassAssignment.Offer_Sent.isnot(None)).count()
    offer_signed = base.filter(StudentClassAssignment.Offer_Signed.is_(True)).count()
    workday = base.filter(StudentClassAssignment.Offer_Signed_Workday.is_(True)).count()
    return _normalized(
        ["Hired", "Offer sent", "Offer signed", "Workday complete"],
        [("Count", [hired, offer_sent, offer_signed, workday])],
    )


@router.get("/enrollment/course-by-term")
def enrollment_course_by_term(metric: str = Query("enrollment", pattern="^(enrollment|fillrate)$"),
                              subject: Optional[str] = Query(None),
                              career: Optional[str] = Query(None),
                              cat_min: Optional[int] = Query(None),
                              cat_max: Optional[int] = Query(None),
                              limit: int = Query(25, ge=1, le=200),
                              db: Session = Depends(get_db),
                              user: dict = Depends(require_perm("analytics"))):
    """
    Cross-term enrollment per COURSE (Subject + CatalogNum), since ClassNum is
    term-specific. Rows = courses, columns = terms. metric: 'enrollment' (raw
    EnrollTotal) or 'fillrate' (EnrollTotal/EnrollCap %). Optional filters:
    subject, career (UGRD/GRAD), CatalogNum range (cat_min/cat_max). Top-N
    courses by total enrollment. Shape feeds the heatmap (course x term).
    """
    q = db.query(
        ClassSchedule.Subject.label("subject"),
        ClassSchedule.CatalogNum.label("cat"),
        ClassSchedule.Term.label("term"),
        func.sum(ClassSchedule.EnrollTotal).label("tot"),
        func.sum(ClassSchedule.EnrollCap).label("cap"),
    ).filter(_enroll_sections())
    if subject:
        q = q.filter(ClassSchedule.Subject == subject)
    if career:
        q = q.filter(ClassSchedule.AcadCareer == career)
    if cat_min is not None:
        q = q.filter(ClassSchedule.CatalogNum >= cat_min)
    if cat_max is not None:
        q = q.filter(ClassSchedule.CatalogNum <= cat_max)
    rows = q.group_by(ClassSchedule.Subject, ClassSchedule.CatalogNum, ClassSchedule.Term).all()
    terms = sorted({r.term for r in rows})
    courses = {}
    for r in rows:
        courses.setdefault(f"{r.subject} {r.cat}", {})[r.term] = (r.tot or 0, r.cap or 0)

    def total(c):
        return sum(t for t, _ in courses[c].values())

    top = sorted(courses, key=total, reverse=True)[:limit]

    def val(c, term):
        tot, cap = courses[c].get(term, (0, 0))
        if metric == "fillrate":
            return round(100.0 * tot / cap, 1) if cap else 0
        return tot

    series = [(c, [val(c, t) for t in terms]) for c in sorted(top)]
    return _normalized(terms, series)


@router.get("/enrollment/subjects")
def enrollment_subjects(db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    """Distinct subjects for the course-report filter dropdown."""
    rows = db.query(ClassSchedule.Subject).distinct().all()
    return sorted({r[0] for r in rows if r[0]})


@router.get("/enrollment/instructors")
def enrollment_instructors(db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    """Instructors who teach enrollment sections — for the instructor-load dropdown."""
    rows = (db.query(ClassSchedule.InstructorID, ClassSchedule.InstructorLastName,
                     ClassSchedule.InstructorFirstName)
            .filter(_enroll_sections()).distinct().all())
    out = {}
    for iid, ln, fn in rows:
        if iid is None:
            continue
        out[iid] = f"{ln or ''}, {fn or ''}".strip().strip(",").strip()
    return [{"id": i, "name": out[i]} for i in sorted(out, key=lambda x: out[x])]


@router.get("/enrollment/catalogs")
def enrollment_catalogs(subject: str = Query(...), db: Session = Depends(get_db),
                        user: dict = Depends(require_perm("analytics"))):
    """Catalog numbers offered for a subject (active enrollment sections)."""
    rows = db.query(ClassSchedule.CatalogNum).filter(
        _enroll_sections(), ClassSchedule.Subject == subject).distinct().all()
    return sorted({r[0] for r in rows if r[0] is not None})


@router.get("/enrollment/course-by-instructor")
def course_by_instructor(subject: str = Query(...), catalog: int = Query(...),
                         metric: str = Query("enrollment", pattern="^(enrollment|fillrate)$"),
                         db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    """For one course (Subject + CatalogNum): per-instructor fill across terms.
    Rows = instructors, columns = terms. metric enrollment | fillrate."""
    rows = (db.query(
                ClassSchedule.InstructorID.label("iid"),
                ClassSchedule.InstructorLastName.label("ln"),
                ClassSchedule.InstructorFirstName.label("fn"),
                ClassSchedule.Term.label("term"),
                func.sum(ClassSchedule.EnrollTotal).label("tot"),
                func.sum(ClassSchedule.EnrollCap).label("cap"))
            .filter(_enroll_sections(), ClassSchedule.Subject == subject,
                    ClassSchedule.CatalogNum == catalog)
            .group_by(ClassSchedule.InstructorID, ClassSchedule.InstructorLastName,
                      ClassSchedule.InstructorFirstName, ClassSchedule.Term)
            .all())
    terms = sorted({r.term for r in rows})
    labels, cells = {}, {}
    for r in rows:
        name = f"{(r.fn or '')[:1]}. {r.ln or ''}".strip()
        labels[r.iid] = f"{name} ({r.iid})" if r.iid else name or "Unknown"
        tot, cap = r.tot or 0, r.cap or 0
        cells[(r.iid, r.term)] = (round(100.0 * tot / cap, 1) if cap else 0) if metric == "fillrate" else tot
    iids = sorted(labels, key=lambda i: labels[i])
    series = [(labels[i], [cells.get((i, t), 0) for t in terms]) for i in iids]
    return _normalized(terms, series)


@router.get("/enrollment/instructor-load")
def instructor_load(instructor_id: int = Query(...), term: Optional[str] = Query(None),
                    db: Session = Depends(get_db), user: dict = Depends(require_perm("analytics"))):
    """All of an instructor's enrollment sections for a term: enrolled vs capacity
    per class (Subject + CatalogNum). Two series so the UI can show the total fill."""
    use_term = term or ACTIVE_TERM
    rows = (db.query(
                ClassSchedule.Subject.label("subject"),
                ClassSchedule.CatalogNum.label("cat"),
                func.sum(ClassSchedule.EnrollTotal).label("tot"),
                func.sum(ClassSchedule.EnrollCap).label("cap"))
            .filter(_enroll_sections(), ClassSchedule.InstructorID == instructor_id,
                    ClassSchedule.Term == use_term)
            .group_by(ClassSchedule.Subject, ClassSchedule.CatalogNum).all())
    rows = sorted(rows, key=lambda r: (r.subject or "", r.cat or 0))
    labels = [f"{r.subject} {r.cat}" for r in rows]
    return _normalized(labels, [
        ("Enrolled", [r.tot or 0 for r in rows]),
        ("Capacity", [r.cap or 0 for r in rows]),
    ])


@router.get("/enrollment/levels")
def enrollment_levels(subject: str = Query(...), db: Session = Depends(get_db),
                      user: dict = Depends(require_perm("analytics"))):
    """Catalog 'hundreds' offered for a subject (active enrollment sections),
    e.g. [100,200,300,400,500,700]. Drives which Level options the UI shows."""
    rows = db.query(ClassSchedule.CatalogNum).filter(
        _enroll_sections(), ClassSchedule.Subject == subject).distinct().all()
    return sorted({(c[0] // 100) * 100 for c in rows if c[0] is not None})
