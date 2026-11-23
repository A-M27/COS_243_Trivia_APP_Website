from typing import Optional
from datetime import datetime, timezone as _tz
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel, EmailStr, Field as PydanticField
import sqlalchemy as sa



def utc_now() -> datetime:
    return datetime.now(_tz.utc)


SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class DeckTagLink(SQLModel, table=True):
    deck_id: Optional[int] = Field(
        default=None, foreign_key="deck.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    Username: str = ""
    First_name: str = ""
    Last_name: str = ""
    email: str = Field(unique=True)
    password_hash: Optional[str] = None
    Location: str = ""
    Timezone: str = ""
    Created_at: datetime = Field(default_factory=utc_now)


class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    expires_at: datetime



class Deck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    User_id: int = Field(foreign_key="user.id")
    Visibility: bool = Field(default=False)
    created_at: datetime = Field(
       default=None,
       nullable=False,
       sa_column_kwargs={"server_default": sa.func.now()},
    )
    updated_at: datetime = Field(
       default=None,
       nullable=False,
       sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )
    archived_at: Optional[datetime] = None

    tags: list["Tag"] = Relationship(
        back_populates="decks", link_model=DeckTagLink
    )


class Card(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    Front: str
    Rear: str
    Deck_id: int = Field(foreign_key="deck.id")
    Card_type: Optional[str] = None
    Created_at: datetime = Field(
       default=None,
       nullable=False,
       sa_column_kwargs={"server_default": sa.func.now()},
    )
    Updated_at: datetime = Field(
       default=None,
       nullable=False,
       sa_column_kwargs={"server_default": sa.func.now(), "onupdate": sa.func.now()},
    )
    suspended: bool = Field(default=False)
    difficulty: int = Field(default=3, sa_column_kwargs={"server_default": "3"})
    display_name: Optional[str] = None




class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    User_id: int = Field(foreign_key="user.id")
    name: str
    Color: Optional[str] = None

    decks: list["Deck"] = Relationship(
        back_populates="tags", link_model=DeckTagLink
    )




class UserForm(BaseModel):
    """Validates user input from the HTML form. Not a database table."""

    username: str = PydanticField(min_length=3, max_length=32)
    email: EmailStr


class RegisterForm(UserForm):
    password: str = PydanticField(min_length=8, max_length=128)



class DeckForm(BaseModel):
    title: str = PydanticField(min_length=1, max_length=100)


class CardForm(BaseModel):
    front: str = PydanticField(min_length=1)
    back: str = PydanticField(min_length=1)





class UserPublic(BaseModel):
    """What the API may show about any user."""

    id: int
    Username: str


class DeckCreate(BaseModel):
    title: str = PydanticField(min_length=1, max_length=100)
    description: Optional[str] = PydanticField(default=None, max_length=500)
    Visibility: bool = False


class DeckUpdate(BaseModel):
    """Every field is optional: leave one out (or send null) to keep it."""

    title: Optional[str] = PydanticField(default=None, min_length=1, max_length=100)
    description: Optional[str] = PydanticField(default=None, max_length=500)
    Visibility: Optional[bool] = None


class DeckRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    Visibility: bool
    User_id: int


class CardCreate(BaseModel):
    Front: str = PydanticField(min_length=1, max_length=1000)
    Rear: str = PydanticField(min_length=1, max_length=1000)
    difficulty: int = PydanticField(default=3, ge=1, le=5)


class CardUpdate(BaseModel):
    Front: Optional[str] = PydanticField(default=None, min_length=1, max_length=1000)
    Rear: Optional[str] = PydanticField(default=None, min_length=1, max_length=1000)
    difficulty: Optional[int] = PydanticField(default=None, ge=1, le=5)


class CardRead(BaseModel):
    id: int
    Deck_id: int
    Front: str
    Rear: str
    difficulty: int
