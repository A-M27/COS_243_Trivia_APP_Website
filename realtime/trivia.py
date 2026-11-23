from datetime import datetime

from sqlmodel import Session, func, or_, select

from database import engine
from models import Card, Deck, User, UserSession


def user_from_token(token: str | None) -> User | None:
    if not token:
        return None
    with Session(engine) as session:
        login = session.exec(select(UserSession).where(UserSession.token == token)).first()
        if login is None or login.expires_at < datetime.now():
            return None
        return session.get(User, login.user_id)


def playable_decks(user_id: int) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(
            select(Deck.id, Deck.title, Deck.User_id, func.count(Card.id))
            .join(Card, Card.Deck_id == Deck.id)
            .where(or_(Deck.User_id == user_id, Deck.Visibility == True))
            .group_by(Deck.id, Deck.title, Deck.User_id)
            .order_by(Deck.title)
        ).all()
        decks = [
            {"id": id, "title": title, "cards": cards, "mine": owner == user_id}
            for id, title, owner, cards in rows
        ]
        return sorted(decks, key=lambda d: not d["mine"])


def load_deck(deck_id: int, user_id: int) -> tuple[str, list[dict]] | None:
    with Session(engine) as session:
        deck = session.get(Deck, deck_id)
        if deck is None or not (deck.Visibility or deck.User_id == user_id):
            return None
        cards = session.exec(select(Card).where(Card.Deck_id == deck_id)).all()
        questions = [
            {"text": card.Front, "answer": card.Rear, "points": card.difficulty * 100}
            for card in cards
        ]
        return deck.title, questions


def normalize(text: str) -> str:
    """Lowercase, and squash runs of spaces, so ' Paris ' matches 'paris'."""
    return " ".join(text.lower().split())
