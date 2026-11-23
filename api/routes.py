from auth import verify_api_csrf
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import User, Deck, Card, Tag
from database import get_session
from auth import require_user, get_owned_deck, get_owned_card
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, or_

from models import (
    User, Deck, Card,
    UserPublic, DeckCreate, DeckUpdate, DeckRead,
    CardCreate, CardUpdate, CardRead, RegisterForm,
)
from database import get_session
from auth import (
    require_user, get_api_user, require_api_user,
    get_visible_deck, get_owned_deck, get_owned_card, hash_password,
)




router = APIRouter(dependencies=[Depends(verify_api_csrf)])






@router.get("/users", response_model=list[UserPublic])
def get_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()



@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users", response_model=UserPublic, status_code=201)
def create_user(user_in: RegisterForm, session: Session = Depends(get_session)):
    taken = session.exec(select(User).where(User.email == user_in.email)).first()
    if taken:
        raise HTTPException(status_code=409, detail="That email is already registered")

    user = User(
        Username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    target = session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    session.delete(target)
    session.commit()









@router.get("/decks/{deck_id}/cards", response_model=list[CardRead])
def list_cards(
    deck_id: int,
    user: Optional[User] = Depends(get_api_user),
    session: Session = Depends(get_session),
):
    deck = get_visible_deck(deck_id, user, session)
    return session.exec(select(Card).where(Card.Deck_id == deck.id)).all()


@router.post("/decks/{deck_id}/cards", response_model=CardRead, status_code=201)
def create_card(
    deck_id: int,
    card_in: CardCreate,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    deck = get_owned_deck(deck_id, user, session)
    card = Card(**card_in.model_dump(), Deck_id=deck.id)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.get("/cards/{card_id}", response_model=CardRead)
def read_card(
    card_id: int,
    user: Optional[User] = Depends(get_api_user),
    session: Session = Depends(get_session),
):
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    get_visible_deck(card.Deck_id, user, session)
    return card


@router.patch("/cards/{card_id}", response_model=CardRead)
def update_card(
    card_id: int,
    card_in: CardUpdate,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    card = get_owned_card(card_id, user, session)
    for field, value in card_in.model_dump(exclude_none=True).items():
        setattr(card, field, value)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(
    card_id: int,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    card = get_owned_card(card_id, user, session)
    session.delete(card)
    session.commit()








"""
@router.post("/decks", status_code=201)
def create_deck(
    deck: Deck,
    tag_names: list[str] = [],
    user: User = Depends(require_user),
    session: Session = Depends(get_session),
):
    for name in tag_names:
        tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if not tag:
            tag = Tag(name=name, User_id=user.id)
        deck.tags.append(tag)

    deck.User_id = user.id
    session.add(deck)
    session.commit()
    session.refresh(deck)
    return deck
"""





@router.get("/decks", response_model=list[DeckRead])
def list_decks(
    user: Optional[User] = Depends(get_api_user),
    session: Session = Depends(get_session),
):
    """Public decks, plus your own when you're logged in."""
    if user is None:
        query = select(Deck).where(Deck.Visibility == True)
    else:
        query = select(Deck).where(or_(Deck.Visibility == True, Deck.User_id == user.id))
    return session.exec(query).all()


@router.get("/decks/{deck_id}", response_model=DeckRead)
def read_deck(
    deck_id: int,
    user: Optional[User] = Depends(get_api_user),
    session: Session = Depends(get_session),
):
    return get_visible_deck(deck_id, user, session)


@router.post("/decks", response_model=DeckRead, status_code=201)
def create_deck(
    deck_in: DeckCreate,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    deck = Deck(**deck_in.model_dump(), User_id=user.id)
    session.add(deck)
    session.commit()
    session.refresh(deck)
    return deck


@router.patch("/decks/{deck_id}", response_model=DeckRead)
def update_deck(
    deck_id: int,
    deck_in: DeckUpdate,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    deck = get_owned_deck(deck_id, user, session)
    for field, value in deck_in.model_dump(exclude_none=True).items():
        setattr(deck, field, value)
    session.add(deck)
    session.commit()
    session.refresh(deck)
    return deck


@router.delete("/decks/{deck_id}", status_code=204)
def delete_deck(
    deck_id: int,
    user: User = Depends(require_api_user),
    session: Session = Depends(get_session),
):
    deck = get_owned_deck(deck_id, user, session)
    for card in session.exec(select(Card).where(Card.Deck_id == deck.id)).all():
        session.delete(card)
    session.delete(deck)
    session.commit()












@router.get("/trivia/decks")
def trivia_decks(user: User = Depends(require_api_user)):
    from realtime.trivia import playable_decks
    return {"username": user.Username, "decks": playable_decks(user.id)}
