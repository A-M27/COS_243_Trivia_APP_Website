import hashlib, hmac, os, secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, Form, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlmodel import Session, select

from database import get_session
from models import Card, Deck, User, UserSession


SESSION_COOKIE = "session_token"
SESSION_LENGTH = timedelta(days=7)
COOKIE_SECURE = False
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32)).encode()




hasher = PasswordHash.recommended()

def hash_password(plain: str) -> str:
    return hasher.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return hasher.verify(plain, hashed)




def make_csrf_token(request: Request) -> str:
    session_id = request.state.session_id
    return hmac.new(SECRET_KEY, session_id.encode(), hashlib.sha256).hexdigest()


def same_origin(request: Request) -> bool:
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return True
    ours = f"{request.url.scheme}://{request.url.netloc}"
    return source == ours or source.startswith(ours + "/")



def verify_csrf(request: Request, csrf_token: str = Form("")):
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    if not same_origin(request):
        raise HTTPException(status_code=403, detail="Request came from another origin")
    expected = make_csrf_token(request)
    if SESSION_COOKIE not in request.cookies or not hmac.compare_digest(
        csrf_token.encode(), expected.encode()
    ):
        raise HTTPException(status_code=403, detail="CSRF token missing or wrong")









def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> Optional[User]:
    request.state.user = None

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None

    login = session.exec(select(UserSession).where(UserSession.token == token)).first()
    if login is None or login.expires_at < datetime.now():
        return None

    user = session.get(User, login.user_id)
    request.state.user = user
    return user


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user



def get_api_user(user: Optional[User] = Depends(get_current_user)) -> Optional[User]:
    """Who is calling the API, or None: the same login as the web pages."""
    return user


def require_api_user(user: Optional[User] = Depends(get_api_user)) -> User:
    """Like require_user, but for JSON clients: 401 instead of a redirect to /login."""
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


def get_visible_deck(deck_id: int, user: Optional[User], session: Session) -> Deck:
    """Return the deck if it's public or `user` owns it. Otherwise raise 404."""
    deck = session.get(Deck, deck_id)
    if deck is None or not (deck.Visibility or (user is not None and deck.User_id == user.id)):
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck




def get_owned_deck(deck_id: int, user: User, session: Session) -> Deck:
    deck = session.get(Deck, deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.User_id != user.id:
        if not deck.Visibility:
            
            raise HTTPException(status_code=404, detail="Deck not found")
        
        raise HTTPException(status_code=403, detail="That isn't your deck")
    return deck




def get_owned_card(card_id: int, user: User, session: Session) -> Card:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    get_owned_deck(card.Deck_id, user, session)
    return card






SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def has_body(request: Request) -> bool:
    """True when the request carries a body (HTTP announces one with one of these headers)."""
    length = request.headers.get("content-length", "0").strip()
    return length != "0" or "transfer-encoding" in request.headers


def is_json(request: Request) -> bool:
    """True when Content-Type says JSON. 'application/json; charset=utf-8' counts."""
    media_type = request.headers.get("content-type", "").split(";")[0]
    return media_type.strip().lower() == "application/json"


def verify_api_csrf(request: Request):
    """Refuse API writes from another origin, and any write whose body isn't JSON."""
    if request.method in SAFE_METHODS:
        return
    if not same_origin(request):
        raise HTTPException(status_code=403, detail="Request came from another origin")
    if request.headers.get("sec-fetch-site") in ("same-site", "cross-site"):
        raise HTTPException(status_code=403, detail="Request came from another origin")
    if has_body(request) and not is_json(request):
        raise HTTPException(status_code=415, detail="Send the body as JSON")



SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def has_body(request: Request) -> bool:
    """True when the request carries a body (HTTP announces one with one of these headers)."""
    length = request.headers.get("content-length", "0").strip()
    return length != "0" or "transfer-encoding" in request.headers


def is_json(request: Request) -> bool:
    """True when Content-Type says JSON. 'application/json; charset=utf-8' counts."""
    media_type = request.headers.get("content-type", "").split(";")[0]
    return media_type.strip().lower() == "application/json"


def verify_api_csrf(request: Request):
    """Refuse API writes from another origin, and any write whose body isn't JSON."""
    if request.method in SAFE_METHODS:
        return
    if not same_origin(request):
        raise HTTPException(status_code=403, detail="Request came from another origin")
    if request.headers.get("sec-fetch-site") in ("same-site", "cross-site"):
        raise HTTPException(status_code=403, detail="Request came from another origin")
    if has_body(request) and not is_json(request):
        raise HTTPException(status_code=415, detail="Send the body as JSON")
