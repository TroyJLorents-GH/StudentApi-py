from fastapi import FastAPI
from routes import student, assignment, class_schedule, application, manage_assignments
from routes import auth, phd_application, faculty, admin_users
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os

app = FastAPI()

# Session middleware (needed for dev cookie auth)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-secret"))

# CORS (if you're calling from localhost:3000 or any frontend)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://blue-moss-0cf2b2f10.1.azurestaticapps.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(assignment.router)
app.include_router(class_schedule.router)
app.include_router(application.router)
app.include_router(manage_assignments.router)
app.include_router(phd_application.router)
app.include_router(faculty.router)
app.include_router(admin_users.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Python API backend"}


# --- Debug/health endpoints ---
@app.get("/healthz")
def healthz():
    return {"ok": True}

DEBUG = os.getenv("DEBUG_ROUTES", "false").lower() == "true"

if DEBUG:
    @app.get("/routes")
    def routes():
        return [{"path": r.path} for r in app.router.routes]
