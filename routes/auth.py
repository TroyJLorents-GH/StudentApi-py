from fastapi import APIRouter, Response, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from database import get_db
from dependencies import current_user

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/ping")
def ping():
    return PlainTextResponse("pong")


@router.get("/dev-impersonate")
def dev_impersonate(asurite: str, response: Response, db: Session = Depends(get_db)):
    """
    DEV ONLY: set a plain-text cookie 'auth' = asurite for impersonation.
    """
    asurite = asurite.lower().strip()
    response.set_cookie("auth", asurite, httponly=True, samesite="lax", secure=False, path="/")
    return {"ok": True, "asurite": asurite}


@router.get("/user")
def get_user(user: dict = Depends(current_user)):
    return user


@router.get("/dev-logout")
def dev_logout(response: Response):
    """DEV ONLY: clear the cookie."""
    response.delete_cookie("auth", path="/")
    return {"ok": True}
