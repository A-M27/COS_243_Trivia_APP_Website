import os
import secrets
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select, or_, text                    
from pydantic import ValidationError
from auth import (COOKIE_SECURE, SESSION_COOKIE, SESSION_LENGTH, hash_password, verify_password, get_current_user, require_user, get_owned_deck, get_owned_card, make_csrf_token, verify_csrf)
from models import User, Deck, Card, Tag, DeckTagLink, UserForm, DeckForm, CardForm, RegisterForm, UserSession



from database import get_session



router = APIRouter(dependencies=[Depends(get_current_user), Depends(verify_csrf)])
templates = Jinja2Templates(directory="templates")
templates.env.globals["csrf_token"] = make_csrf_token
templates.env.globals["vite_dev"] = os.environ.get("VITE_DEV") == "1"




@router.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"title": "Flashcard App"}
    )

@router.get("/users")
def users_page(request: Request, session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return templates.TemplateResponse(
        request=request,
        name="users/list.html",
        context={"users": users, "active": "users"},
    )


"""

@router.post("/throwaway")
def throwaway():
    return {"ok": True}

"""






"""
@router.get("/users/new")
def new_user_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="users/form.html",
        context={
            "heading": "New user",
            "action": "/users",
            "values": {},
            "errors": {},
            "active": "users",
        },
    )
"""





"""
@router.post("/users")
def create_user_page(
    username: str = Form(...),
    email: str = Form(...),
    session: Session = Depends(get_session),
):
    user = User(Username=username, email=email)
    session.add(user)
    session.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)
"""




def collect_errors(exc: ValidationError) -> dict:
    """Turn a Pydantic ValidationError into {field_name: message}."""
    return {err["loc"][0]: err["msg"] for err in exc.errors()}



"""
@router.post("/users")
def create_user_page(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    session: Session = Depends(get_session),
):
    values = {"username": username.strip(), "email": email.strip().lower()}

    try:
        form = UserForm(**values)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="users/form.html",
            context={
                "heading": "New user",
                "action": "/users",
                "values": values,
                "errors": collect_errors(exc),
                "active": "users",
            },
            status_code=400,
        )

    taken = session.exec(select(User).where(func.lower(User.email) == form.email.lower())).first()
    if taken:
        return templates.TemplateResponse(
            request=request,
            name="users/form.html",
            context={
                "heading": "New user",
                "action": "/users",
                "values": values,
                "errors": {"email": "That email is already registered."},
                "active": "users",
            },
            status_code=400,
        )

    session.add(User(Username=form.username, email=form.email))
    session.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)
"""






@router.get("/users/{user_id}/edit")
def edit_user_form(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="That isn't your account")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        request=request,
        name="users/form.html",
        context={
            "heading": f"Edit {user.Username}",
            "action": f"/users/{user.id}/edit",
            "values": {"username": user.Username, "email": user.email},
            "errors": {},
            "active": "users",
        },
    )



@router.post("/users/{user_id}/edit")
def update_user_page(
    user_id: int,
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="That isn't your account")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    values = {"username": username.strip(), "email": email.strip().lower()}

    try:
        form = UserForm(**values)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="users/form.html",
            context={
                "heading": f"Edit {user.Username}",
                "action": f"/users/{user_id}/edit",
                "values": values,
                "errors": collect_errors(exc),
                "active": "users",
            },
            status_code=400,
        )

    taken = session.exec(
        select(User).where(func.lower(User.email) == form.email.lower(), User.id != user_id)
    ).first()
    if taken:
        return templates.TemplateResponse(
            request=request,
            name="users/form.html",
            context={
                "heading": f"Edit {user.Username}",
                "action": f"/users/{user_id}/edit",
                "values": values,
                "errors": {"email": "That email is already registered."},
                "active": "users",
            },
            status_code=400,
        )

    user.Username = form.username
    user.email = form.email
    session.add(user)
    session.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)



@router.post("/users/{user_id}/delete")
def delete_user_page(
    user_id: int,
    current_user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="That isn't your account")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)






"""
CURRENT_USER_ID = 1
"""


def parse_tags(raw: str) -> list[str]:
    """'python, web , python' -> ['python', 'web']"""
    names = []
    seen = set()
    for chunk in raw.split(","):
        name = chunk.strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        names.append(name)
    return names


def resolve_tags(names: list[str], session: Session, user: User) -> list[Tag]:
    """Look each name up, creating the Tag only when it's new."""
    tags = []
    for name in names:
        tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if not tag:
            """
            tag = Tag(name=name, User_id=CURRENT_USER_ID)
            """
            tag = Tag(name=name, User_id=user.id)      
        tags.append(tag)
    return tags


@router.get("/decks")
def decks_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    According to the step 5 of the reading, I had to comment out or delete this section because this page showed all the decks to all the users
    decks = session.exec(select(Deck)).all()
    """
    if user:
        query = select(Deck).where(or_(Deck.Visibility == True, Deck.User_id == user.id))
    else:
        query = select(Deck).where(Deck.Visibility == True)
    decks = session.exec(query).all()

    return templates.TemplateResponse(
        request=request,
        name="decks/list.html",
        context={"decks": decks, "active": "decks"},
    )



DECK_SEARCH = """
    SELECT id, title
      FROM deck
     WHERE ("Visibility" = 1 OR "User_id" = :user_id)
       AND title LIKE :pattern ESCAPE '!'
     ORDER BY title
"""


def like_pattern(term: str) -> str:
    """'100%' -> '%100!%%', so the user's own % and _ match only themselves."""
    for ch in "!%_":
        term = term.replace(ch, "!" + ch)
    return f"%{term}%"


@router.get("/search")
def search_page(request: Request, q: str = "", user: Optional[User] = Depends(get_current_user), session: Session = Depends(get_session),):
    q = q.strip()
    decks = []
    if q:
        decks = session.exec(
            text(DECK_SEARCH),
            params={
                "user_id": user.id if user else None,
                "pattern": like_pattern(q),
            },
        ).mappings().all()

    return templates.TemplateResponse(
        request=request,
        name="decks/search.html",
        context={"q": q, "decks": decks, "active": "search"},
    )



@router.get("/decks/new")
def new_deck_form(
    request: Request,
    user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        request=request,
        name="decks/form.html",
        context={
            "heading": "New deck",
            "action": "/decks",
            "values": {},
            "errors": {},
            "active": "decks",
        },
    )


@router.post("/decks")
def create_deck_page(
    request: Request,
    title: str = Form(""),
    tags: str = Form(""),
    is_public: bool = Form(False),                
    user: User = Depends(require_user),           
    session: Session = Depends(get_session),
):
    """
    According to the step 3 of the reading, I had to comment out or delete this section because the owner no longer goes through the form
    values = {"title": title.strip(), "user_id": CURRENT_USER_ID, "tags": tags.strip()}
    """
    values = {"title": title.strip(), "tags": tags.strip(), "is_public": is_public}

    try:
        form = DeckForm(**values)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="decks/form.html",
            context={
                "heading": "New deck",
                "action": "/decks",
                "values": values,
                "errors": collect_errors(exc),
                "active": "decks",
            },
            status_code=400,
        )

    """
    According to step 3 I had to delete or comment out or comment out the following lines because the login guarantees the owner exists
    owner = session.get(User, form.user_id)
    if not owner:
        return templates.TemplateResponse(
            request=request,
            name="decks/form.html",
            context={
                "heading": "New deck",
                "action": "/decks",
                "values": values,
                "errors": {"user_id": "That user does not exist."},
                "active": "decks",
            },
            status_code=400,
        )
    """

    """
    According to steps 3 and 5, I had to delete or comment out the following lines because the owner now comes from the logged-in user and not the form:
    deck = Deck(title=form.title, User_id=form.user_id)
    deck.tags = resolve_tags(parse_tags(values["tags"]), session)
    """
    deck = Deck(title=form.title, User_id=user.id, Visibility=is_public)
    deck.tags = resolve_tags(parse_tags(values["tags"]), session, user)
    session.add(deck)
    session.commit()

    return RedirectResponse(url="/decks", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/decks/{deck_id}/edit")
def edit_deck_form(
    deck_id: int,
    request: Request,
    user: User = Depends(require_user),           
    session: Session = Depends(get_session),
):
    """
    According to step 4, I had to delete or comment out the following lines because the owner now comes from the logged-in user and not the form:
    deck = session.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    """
    deck = get_owned_deck(deck_id, user, session)

    return templates.TemplateResponse(
        request=request,
        name="decks/form.html",
        context={
            "heading": f"Edit {deck.title}",
            "action": f"/decks/{deck.id}/edit",
            "values": {
                "title": deck.title,
                "tags": ", ".join(tag.name for tag in deck.tags),
                "is_public": deck.Visibility,
            },
            "errors": {},
            "active": "decks",
        },
    )


@router.post("/decks/{deck_id}/edit")
def update_deck_page(
    deck_id: int,
    request: Request,
    title: str = Form(""),
    tags: str = Form(""),
    is_public: bool = Form(False),                
    user: User = Depends(require_user),           
    session: Session = Depends(get_session),
):
    """
    According to step 4, I had to delete or comment out the following lines because the owner now comes from the logged-in user and not the form:
    deck = session.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    """
    deck = get_owned_deck(deck_id, user, session)

    """
    According to steps 3 and 5, I had to delete or comment out the following lines:
    values = {"title": title.strip(), "user_id": deck.User_id, "tags": tags.strip()}
    """
    values = {"title": title.strip(), "tags": tags.strip(), "is_public": is_public}   

    try:
        form = DeckForm(**values)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="decks/form.html",
            context={
                "heading": f"Edit {deck.title}",
                "action": f"/decks/{deck_id}/edit",
                "values": values,
                "errors": collect_errors(exc),
                "active": "decks",
            },
            status_code=400,
        )

    deck.title = form.title
    deck.Visibility = is_public                                           
    """
    According to step 3, I had to delete or comment out the following lines:
    deck.tags = resolve_tags(parse_tags(values["tags"]), session)
    """
    deck.tags = resolve_tags(parse_tags(values["tags"]), session, user)   
    session.add(deck)
    session.commit()

    return RedirectResponse(url="/decks", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/decks/{deck_id}/delete")
def delete_deck_page(
    deck_id: int,
    user: User = Depends(require_user),           
    session: Session = Depends(get_session),
):
    """
    According to step 4, I had to delete or comment out the following lines because the owner now comes from the logged-in user and not the form:
    deck = session.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    """
    deck = get_owned_deck(deck_id, user, session)

    session.delete(deck)
    session.commit()

    return RedirectResponse(url="/decks", status_code=status.HTTP_303_SEE_OTHER)



@router.get("/decks/{deck_id}")
def deck_detail_page(
    deck_id: int,
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    deck = session.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    is_owner = user is not None and deck.User_id == user.id
    if not deck.Visibility and not is_owner:
        raise HTTPException(status_code=404, detail="Deck not found")

    owner = session.get(User, deck.User_id)
    cards = session.exec(select(Card).where(Card.Deck_id == deck_id)).all()

    return templates.TemplateResponse(
        request=request,
        name="decks/detail.html",
        context={
            "deck": {
                "id": deck.id,
                "title": deck.title,
                "username": owner.Username if owner else "(unknown)",
                "tags": ", ".join(tag.name for tag in deck.tags),
                "is_owner": is_owner,
            },
            "cards": [
                {"id": card.id, "front": card.Front, "back": card.Rear}
                for card in cards
            ],
            "active": "decks",
        },
    )



@router.get("/decks/{deck_id}/cards/new")
def new_card_form(
    deck_id: int,
    request: Request,
    user: User = Depends(require_user),           
    session: Session = Depends(get_session),
):
    """
    According to step 4 of the reading I am supposed to replace this with get_owned_deck.
    deck = session.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    """
    deck = get_owned_deck(deck_id, user, session)

    return templates.TemplateResponse(
        request=request,
        name="cards/form.html",
        context={
            "heading": f"New card in {deck.title}",
            "action": f"/decks/{deck_id}/cards",
            "cancel": f"/decks/{deck_id}",
            "values": {},
            "errors": {},
            "active": "decks",
        },
    )


@router.post("/decks/{deck_id}/cards")
def create_card_page(
    deck_id: int,
    request: Request,
    front: str = Form(""),
    back: str = Form(""),
    user: User = Depends(require_user),          
    session: Session = Depends(get_session),
):
    """
    According to step 4 of the reading I am supposed to replace this with get_owned_deck.
    deck = session.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    """
    deck = get_owned_deck(deck_id, user, session)

    values = {"front": front.strip(), "back": back.strip()}

    try:
        form = CardForm(**values)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="cards/form.html",
            context={
                "heading": f"New card in {deck.title}",
                "action": f"/decks/{deck_id}/cards",
                "cancel": f"/decks/{deck_id}",
                "values": values,
                "errors": collect_errors(exc),
                "active": "decks",
            },
            status_code=400,
        )

    session.add(Card(Front=form.front, Rear=form.back, Deck_id=deck_id))
    session.commit()

    return RedirectResponse(
        url=f"/decks/{deck_id}", status_code=status.HTTP_303_SEE_OTHER
    )





@router.get("/cards/{card_id}/edit")
def edit_card_form(
    card_id: int,
    request: Request,
    user: User = Depends(require_user),           
    session: Session = Depends(get_session),
):
    """
    According to step 4 of the reading I am supposed to replace this with get_owned_card.
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    """
    card = get_owned_card(card_id, user, session)

    return templates.TemplateResponse(
        request=request,
        name="cards/form.html",
        context={
            "heading": "Edit card",
            "action": f"/cards/{card.id}/edit",
            "cancel": f"/decks/{card.Deck_id}",
            "values": {"front": card.Front, "back": card.Rear},
            "errors": {},
            "active": "decks",
        },
    )


@router.post("/cards/{card_id}/edit")
def update_card_page(
    card_id: int,
    request: Request,
    front: str = Form(""),
    back: str = Form(""),
    user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    """
    According to step 4 of the reading I am supposed to replace this with get_owned_card.
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    """
    card = get_owned_card(card_id, user, session)

    values = {"front": front.strip(), "back": back.strip()}

    try:
        form = CardForm(**values)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="cards/form.html",
            context={
                "heading": "Edit card",
                "action": f"/cards/{card_id}/edit",
                "cancel": f"/decks/{card.Deck_id}",
                "values": values,
                "errors": collect_errors(exc),
                "active": "decks",
            },
            status_code=400,
        )

    card.Front = form.front
    card.Rear = form.back
    deck_id = card.Deck_id
    session.add(card)
    session.commit()

    return RedirectResponse(
        url=f"/decks/{deck_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/cards/{card_id}/delete")
def delete_card_page(
    card_id: int,
    user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    """
    According to step 4 of the reading I am supposed to replace this with get_owned_card.
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    """
    card = get_owned_card(card_id, user, session)

    deck_id = card.Deck_id
    session.delete(card)
    session.commit()

    return RedirectResponse(
        url=f"/decks/{deck_id}", status_code=status.HTTP_303_SEE_OTHER
    )




@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={"values": {}, "errors": {}, "active": "register"},
    )


@router.post("/register")
def register(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    session: Session = Depends(get_session),
):

    values = {"username": username.strip(), "email": email.strip().lower()}
    ctx = {"values": values, "active": "register"}

    try:
        form = RegisterForm(**values, password=password)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={**ctx, "errors": collect_errors(exc)},
            status_code=400,
        )

    taken = session.exec(select(User).where(func.lower(User.email) == form.email.lower())).first()
    if taken:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={**ctx, "errors": {"email": "That email is already registered."}},
            status_code=400,
        )

    session.add(
        User(
            Username=form.username,
            email=form.email,
            password_hash=hash_password(form.password),
        )
    )
    session.commit()

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={"values": {}, "error": None, "active": "login"},
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    session: Session = Depends(get_session),
):
    email = email.strip().lower()
    user = session.exec(select(User).where(func.lower(User.email) == email)).first()

    valid = ( user is not None and user.password_hash is not None and verify_password(password, user.password_hash) )
    if not valid:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "values": {"email": email},
                "error": "Email or password is incorrect.",
                "active": "login",
            },
            status_code=400,
        )

    token = secrets.token_urlsafe(32)
    session.add(
        UserSession(
            token=token,
            user_id=user.id,
            expires_at=datetime.now() + SESSION_LENGTH,
        )
    )
    session.commit()

    response = RedirectResponse(url="/decks", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=int(SESSION_LENGTH.total_seconds()),
    )
    return response



@router.post("/logout")
def logout(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        login = session.exec(
            select(UserSession).where(UserSession.token == token)
        ).first()
        if login:
            session.delete(login)
            session.commit()

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.post("/logout-everywhere")
def logout_everywhere(
    user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    logins = session.exec(
        select(UserSession).where(UserSession.user_id == user.id)
    ).all()
    for login in logins:
        session.delete(login)
    session.commit()

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/decks/{deck_id}/study")
def study_page(deck_id: int, request: Request):
    return templates.TemplateResponse(
        request=request,
        name="decks/study.html",
        context={"deck_id": deck_id, "active": "decks"},
    )

@router.get("/trivia/")
def trivia_page(request: Request, user: User = Depends(require_user),
    session: Session = Depends(get_session),):
    return templates.TemplateResponse(
        request=request,
        name="trivia.html",
        context={"active": "trivia"},
    )





