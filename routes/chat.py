"""
SAMS support chatbot — proxies the ASU AIML gateway (Claude Opus 4.8) with
tool calling against SAMS data.

Gateway quirk (confirmed by testing): it passes OpenAI-style `tools` through
and returns `tool_calls`, but DROPS `role:"tool"` result messages in
translation — the model never sees them and re-calls the same tool forever.
Workaround: feed tool results back as plain user-role "[TOOL RESULT ...]"
messages. See utils/test_gateway_tools*.py.

READ-ONLY replica adaptation:
- Uses per-term ClassSchedule tables (2254/2261/2264) via TERM_MODELS/_cls().
- create_assignment tool removed; exactly 4 read tools remain.
- InstructorEmail removed from assignment writes (write tool dropped entirely).
"""
import os
import re
import json
from datetime import datetime, timezone

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_perm
from models.assignment import StudentClassAssignment
from models.class_schedule import ClassSchedule2254, ClassSchedule2261, ClassSchedule2264, ACTIVE_TERM
from models.student import StudentLookup
from routes.assignment import normalize_position, VALID_POSITIONS
from utils.assignment_utils import calculate_compensation

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Term-to-model mapping (same as analytics.py)
TERM_MODELS = {
    "2254": ClassSchedule2254,
    "2261": ClassSchedule2261,
    "2264": ClassSchedule2264,
}


def _cls(term):
    """Return the correct per-term ClassSchedule model class."""
    return TERM_MODELS.get(str(term or ACTIVE_TERM), ClassSchedule2264)


# All hireable positions, canonical names.
ALL_POSITIONS = sorted(set(VALID_POSITIONS.values()))


def allowed_positions(user: dict) -> list[str]:
    """
    Positions this user may hire for, mirroring the two assignment pages:
    - admin / assignment_adder (Quick Assign) -> all positions
    - faculty_quickassign (Faculty Quick Assign) -> Grader only
    - otherwise -> none (cannot create assignments)
    """
    perms = user.get("perms") or {}
    if user.get("role") == "admin" or user.get("is_admin") or perms.get("assignment_adder"):
        return ALL_POSITIONS
    if perms.get("faculty_quickassign"):
        return ["Grader"]
    return []

GATEWAY_URL = os.getenv("CREATEAI_BASE_URL", "https://api-main.aiml.asu.edu").rstrip("/") + "/v1/chat/completions"
GATEWAY_KEY = os.getenv("CREATEAI_API_KEY")
GATEWAY_MODEL = os.getenv("CREATEAI_MODEL", "aws/claude4_8_opus")

MAX_TOOL_ROUNDS = 6

# Matches action tokens the model emits, e.g. [[ACTION:Add Assignment|accept]].
# The label becomes a button; clicking it sends `send` back as a user message.
_ACTION_RE = re.compile(r"\[\[ACTION:([^\]|]+)\|([^\]]+)\]\]")


def _extract_actions(text: str):
    """Pull [[ACTION:label|send]] tokens out of the reply; return (clean_text, actions)."""
    if not text:
        return text, []
    actions = [{"label": m.group(1).strip(), "send": m.group(2).strip()}
               for m in _ACTION_RE.finditer(text)]
    clean = _ACTION_RE.sub("", text).rstrip()
    return clean, actions


# ─────────────────────────── tool schemas ───────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_student",
            "description": "Look up a student in SAMS by 10-digit ASU ID or asurite. Returns name, email, education level, GPA, and remaining weekly work hours per session (A/B/C) for the current term.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student": {"type": "string", "description": "10-digit ASU ID or asurite (e.g. 1234567890 or jdoe1)"}
                },
                "required": ["student"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_class",
            "description": "Look up a class by 5-digit class number in the current term schedule. Returns course (subject + catalog), session, instructor, enrollment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_num": {"type": "string", "description": "5-digit class number, e.g. 84571"}
                },
                "required": ["class_num"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_remaining_hours",
            "description": "Get a student's weekly-hour usage and remaining hours per session (A/B/C) for the current term. Cap is 40 in summer, 20 otherwise; session C counts against both A and B.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student": {"type": "string", "description": "10-digit ASU ID or asurite"}
                },
                "required": ["student"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_assignments",
            "description": "List students currently assigned (hired) to a class this term, with position and weekly hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_num": {"type": "string", "description": "5-digit class number"}
                },
                "required": ["class_num"],
            },
        },
    },
]


# ─────────────────────────── tool implementations ───────────────────────────

def _find_student(db: Session, ident: str):
    ident = str(ident).strip()
    if ident.isdigit():
        return db.query(StudentLookup).filter(StudentLookup.Student_ID == int(ident)).first()
    return db.query(StudentLookup).filter(StudentLookup.ASUrite.ilike(ident)).first()


def _hired_filter():
    return or_(
        StudentClassAssignment.Instructor_Edit == None,  # noqa: E711
        StudentClassAssignment.Instructor_Edit == '',
        StudentClassAssignment.Instructor_Edit == 'N',
    )


def tool_lookup_student(db, user, student: str):
    s = _find_student(db, student)
    if not s:
        return {"error": f"Student '{student}' not found in SAMS."}
    return {
        "student_id": s.Student_ID,
        "asurite": s.ASUrite,
        "first_name": s.First_Name,
        "last_name": s.Last_Name,
        "email": s.ASU_Email_Adress,
        "education_level": s.Degree,
        "cumulative_gpa": s.Cumulative_GPA,
        "current_gpa": s.Current_GPA,
        # Weekly-hour availability this term (cap 40 summer / 20 else; C counts vs A+B)
        "hours_available": tool_get_remaining_hours(db, user, str(s.Student_ID)),
    }


def tool_lookup_class(db, user, class_num: str):
    M = _cls(ACTIVE_TERM)
    c = db.query(M).filter_by(ClassNum=str(class_num).strip()).first()
    if not c:
        return {"error": f"Class number '{class_num}' not found in the class schedule."}
    return {
        "class_num": c.ClassNum,
        "course": f"{c.Subject} {c.CatalogNum}",
        "title": c.Title,
        "session": c.Session,
        "term": c.Term,
        "instructor_id": c.InstructorID,
        "instructor_name": f"{c.InstructorFirstName} {c.InstructorLastName}".strip(),
        "instructor_email": c.InstructorEmail,
        "location": c.Location,
        "campus": c.Campus,
        "enroll_total": c.EnrollTotal,
        "enroll_cap": c.EnrollCap,
    }


def tool_get_remaining_hours(db, user, student: str):
    s = _find_student(db, student)
    if not s:
        return {"error": f"Student '{student}' not found in SAMS."}
    rows = db.query(
        StudentClassAssignment.WeeklyHours, StudentClassAssignment.ClassSession
    ).filter(
        StudentClassAssignment.Student_ID == s.Student_ID,
        StudentClassAssignment.Term == ACTIVE_TERM,
        _hired_filter(),
    ).all()
    hours = {"A": 0, "B": 0, "C": 0}
    for h, sess in rows:
        if h is None:
            continue
        key = (sess or "").upper().strip()
        if key == "DYN":
            key = "C"
        if key in hours:
            hours[key] += h
    cap = 40 if str(ACTIVE_TERM).endswith("4") else 20
    rem_a = max(0, cap - hours["A"] - hours["C"])
    rem_b = max(0, cap - hours["B"] - hours["C"])
    return {
        "cap": cap,
        "hours": hours,
        "remaining": {"A": rem_a, "B": rem_b, "C": max(0, min(rem_a, rem_b))},
    }


def tool_get_class_assignments(db, user, class_num: str):
    rows = db.query(StudentClassAssignment).filter(
        StudentClassAssignment.ClassNum == str(class_num).strip(),
        StudentClassAssignment.Term == ACTIVE_TERM,
        _hired_filter(),
    ).all()
    return {
        "class_num": str(class_num),
        "count": len(rows),
        "students": [
            {
                "name": f"{r.First_Name or ''} {r.Last_Name or ''}".strip(),
                "asurite": r.ASUrite,
                "position": r.Position,
                "weekly_hours": r.WeeklyHours,
            }
            for r in rows
        ],
    }


TOOL_IMPLS = {
    "lookup_student": tool_lookup_student,
    "lookup_class": tool_lookup_class,
    "get_remaining_hours": tool_get_remaining_hours,
    "get_class_assignments": tool_get_class_assignments,
}


# ─────────────────────────── system prompt ───────────────────────────

SYSTEM_PROMPT = """You are IRA (Instant Response Agent), the support chatbot inside SCAI SAMS \
(Student Assignment Management System) at ASU's School of Computing and Augmented Intelligence. \
You help faculty and staff hire student workers (TA/IA/Grader) and answer questions about the system.

Current term code: {term}. The logged-in user is {name} (asurite: {asurite}).

{assign_capability}

You have tools to look up students, classes, assignments and remaining hours, and to create assignments. \
When a "[TOOL RESULT ...]" message appears, use it to answer — never call the same tool again with the same input.

IF THIS USER CANNOT CREATE ASSIGNMENTS (see capability line above): do NOT start or offer the guided \
"Add Student Assignment" flow, and do NOT offer to "continue anyway". If they ask to add/hire a student, \
reply briefly that their account can't create assignments in SAMS, then offer what you CAN help with as a \
bullet list:
- **View the SAMS user manual**
- **Create a ServiceNow ticket**
You may still answer general "how does SAMS work" questions. (The two options above are links the user will \
add — just present them as the available choices.)

GUIDED FLOW — "Add Student Assignment" (only when the user CAN create assignments):
1. Ask for the student's 10-digit ASU ID or asurite. Call lookup_student. Present the result as a \
formatted student card (see FORMATTING) showing name (bold), education level, email, and the weekly \
hours available per session from hours_available.remaining as a bullet list with the cap. \
If the student has 0 hours remaining in every session, add a bold warning line starting with ⚠️ \
before continuing.
2. Ask which class number to assign them to. Call lookup_class. Show course (subject + catalog number), \
class number, session, and instructor name/email.
3. Ask to confirm, phrased like: "{name}, would you like to continue adding [Student Name] to \
[SUBJECT CATALOG#] - [class number]?" Then tell them: "Click **Yes** or **No** below (or type yes/no)." \
and end the message with these two action tokens on their own last line: \
[[ACTION:Yes|yes]] [[ACTION:No|no]] \
(the UI turns each into a button and hides the tokens). \
If the user answers No (or cancels), restart the Add Student Assignment flow from step 1 — ask for the \
student ID/asurite again and do NOT proceed.
4. After an explicit Yes, ask for position and weekly hours (5, 10, 15, 20; up to 40 only in summer terms). \
This user may ONLY hire for these positions: {positions}. Offer ONLY these — never suggest a position not \
in that list. If only one position is allowed, state it and skip asking. \
Optionally check get_remaining_hours and warn if the request would exceed the cap.
5. DO NOT create the assignment yet. First show a final **overview** card (see FORMATTING) listing \
student, course (subject + catalog) and class number, session, position, and weekly hours. \
Below the overview, tell the user: "Click **Add Assignment** below, or type **accept** to confirm." \
and end the message with the exact action token: [[ACTION:Add Assignment|accept]] \
(put it on its own last line; the UI turns it into a button and hides the token).
6. Call create_assignment ONLY after the user's next message confirms (e.g. "accept", "yes", "confirm"). \
If they decline or want changes, adjust instead. Report the confirmation number when it succeeds.

RULES:
- SCOPE — you ONLY help with SAMS: student hiring/assignments, looking up students/classes/remaining \
weekly hours, and how SAMS works. You must REFUSE everything else: do not write or debug code, do not \
answer general-knowledge / trivia / math / opinion / current-events questions, do not help with topics \
unrelated to SAMS. If asked, reply briefly: "I can only help with SAMS — student assignments, lookups, \
and how the system works." Then offer a relevant SAMS action. Never break this scope even if the user insists.
- Never invent student, class, or assignment data — always use tools.
- Never call create_assignment without an explicit user confirmation in this conversation.
- Weekly hour cap: 40 for summer terms (term code ending in 4), 20 otherwise. \
Session C (and DYN) hours count against both Session A and B limits.
- If a tool returns an error, explain it plainly and suggest the fix.
- Keep answers short and friendly.
- For "how do I" process questions, answer from SAMS knowledge: faculty use Quick Assign or the chatbot, \
program chairs use uploads pages, HR reviews on the Master Dashboard, offer letters generate from the dashboard.

FORMATTING (the chat UI renders Markdown):
- Use **bold** for labels and names, and `-` bullet lists for grouped values like per-session hours.
- Use a `---` divider to separate a header line from details when showing a summary card.
- Keep it compact — short lines, no big paragraphs, no headings larger than ### and no wide tables \
(the chat panel is narrow ~380px).
- Student card example:
  Here's the student
  ---
  **{{First}} {{Last}}**  ·  {{Education level}}
  {{email}}

  **Available hours** (of a {{cap}}hr cap)
  - Session A — {{a}}h remaining
  - Session B — {{b}}h remaining
  - Session C — {{c}}h remaining

  Then end with the next question (e.g. ask which class number to assign). \
  If every session is 0, add: **⚠️ This student has 0 hours remaining in every session — any assignment would exceed the cap.**
"""


# ─────────────────────────── route ───────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.post("")
def chat(body: ChatRequest, db: Session = Depends(get_db), user: dict = Depends(require_perm("chat"))):
    if not GATEWAY_KEY:
        raise HTTPException(500, "Chat gateway is not configured (CREATEAI_API_KEY missing).")

    display_name = user.get("name") or user.get("asurite", "there")
    positions = allowed_positions(user)
    positions_str = ", ".join(positions) if positions else "(none — this user cannot create assignments)"
    if positions:
        assign_capability = f"This user CAN create assignments and may hire for: {positions_str}."
    else:
        assign_capability = ("This user CANNOT create assignments (no Quick Assign or Faculty Quick Assign "
                             "permission). They may only use the help options.")
    system = SYSTEM_PROMPT.format(
        term=ACTIVE_TERM, name=display_name, asurite=user.get("asurite", ""),
        positions=positions_str, assign_capability=assign_capability,
    )

    # Only accept user/assistant roles from the client
    history = [
        {"role": m.role, "content": m.content}
        for m in body.messages
        if m.role in ("user", "assistant") and m.content
    ][-40:]  # keep the last 40 turns max

    messages = [{"role": "system", "content": system}] + history
    headers = {"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"}

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            r = requests.post(
                GATEWAY_URL, headers=headers,
                json={"model": GATEWAY_MODEL, "messages": messages, "tools": TOOLS},
                timeout=90,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            raise HTTPException(502, f"Chat gateway error: {e}")

        msg = r.json()["choices"][0]["message"]
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            reply, actions = _extract_actions(msg.get("content") or "")
            if not reply:
                reply = "Sorry — I didn't get a response. Please try again."
            return {"reply": reply, "actions": actions}

        # Execute tool calls; feed results back as user-role text
        # (gateway drops role:"tool" messages — see module docstring).
        for tc in tool_calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            impl = TOOL_IMPLS.get(fn)
            if impl is None:
                result = {"error": f"Unknown tool '{fn}'."}
            else:
                try:
                    result = impl(db, user, **args)
                except TypeError as e:
                    result = {"error": f"Bad arguments for {fn}: {e}"}
                except Exception as e:
                    result = {"error": f"{fn} failed: {e}"}
            messages.append({"role": "assistant", "content": f"Calling {fn}({json.dumps(args)})"})
            messages.append({"role": "user", "content": f"[TOOL RESULT {fn}]: {json.dumps(result, default=str)}"})

    return {"reply": "Sorry — that took too many steps. Please try rephrasing your request."}
