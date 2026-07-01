import os
from fastapi import APIRouter, Response, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from database import get_db
from dependencies import current_user

router = APIRouter(prefix="/api", tags=["auth"])

# Cookie policy. Local dev (same-site): lax / not-secure (defaults).
# Deployed portfolio (frontend and backend on different Azure domains =
# cross-site): set COOKIE_SAMESITE=none and COOKIE_SECURE=true in App Service
# config, else the browser drops the auth cookie on cross-site fetches.
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


@router.get("/ping")
def ping():
    return PlainTextResponse("pong")


@router.get("/dev-impersonate")
def dev_impersonate(asurite: str, response: Response, db: Session = Depends(get_db)):
    """
    DEV ONLY: set a plain-text cookie 'auth' = asurite for impersonation.
    """
    asurite = asurite.lower().strip()
    response.set_cookie("auth", asurite, httponly=True, samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE, path="/")
    return {"ok": True, "asurite": asurite}


@router.get("/user")
def get_user(user: dict = Depends(current_user)):
    return user


@router.get("/dev-logout")
def dev_logout(response: Response):
    """DEV ONLY: clear the cookie."""
    response.delete_cookie("auth", path="/", samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE)
    return {"ok": True}
