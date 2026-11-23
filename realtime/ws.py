import random

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from auth import SESSION_COOKIE
from realtime.trivia import load_deck, normalize, user_from_token
from realtime.ws_manager import (
    CLOSE_ALREADY_STARTED,
    CLOSE_BAD_SETTINGS,
    CLOSE_GAME_FULL,
    CLOSE_NAME_TAKEN,
    CLOSE_NO_GAME,
    CLOSE_NOT_LOGGED_IN,
    MAX_PLAYERS,
    MIN_PLAYERS,
    Room,
    manager,
)

router = APIRouter()

REACTIONS = ("👍", "😂", "🔥", "🎉", "🤯")


async def send_question(room: Room):
    q = room.current_question()
    if q is None:
        await room.broadcast_json({"type": "question", "question": None})
        return
    await room.broadcast_json({
        "type": "question",
        "question": {
            "number": room.current + 1,
            "total": len(room.questions),
            "text": q["text"],
            "points": q["points"],
        },
    })


async def start_round(room: Room):
    found = load_deck(room.deck_id, room.host_user_id)
    if found is None:
        return
    title, questions = found
    if not questions:
        return
    random.shuffle(questions)
    questions = questions[: room.count]

    room.questions = questions
    room.current = 0
    room.scores = {}
    room.started = True

    await room.broadcast_json({"type": "start"})
    await room.broadcast_json({"type": "scores", "scores": room.scores})
    await room.say(f"Let's play {title}: {len(questions)} questions. Good luck!")
    await send_question(room)


async def end_round(room: Room):
    """The last question is over: announce the winner, or the tie."""
    if not room.scores:
        await room.say("That's the last question, and nobody scored.")
        return
    best = max(room.scores.values())
    winners = [n for n, s in room.scores.items() if s == best]
    if len(winners) == 1:
        result = f"{winners[0]} wins!"
    else:
        result = "It's a tie between " + " and ".join(winners) + "!"
    for winner in winners:
        room.wins[winner] = room.wins.get(winner, 0) + 1
    await room.broadcast_json({"type": "wins", "wins": room.wins})
    await room.say(f"That's the last question. {result}")


async def skip_question(room: Room, name: str):
    q = room.current_question()
    if q is None:
        return
    room.current += 1
    await room.say(f"{name} skipped. The answer was: {q['answer']}")
    await send_question(room)
    if room.current_question() is None:
        await end_round(room)


async def react(room: Room, name: str, message_id, emoji):
    if not isinstance(message_id, int) or emoji not in REACTIONS:
        return
    reactions = room.toggle_reaction(message_id, emoji, name)
    if reactions is None:
        return
    await room.broadcast_json({"type": "reactions", "id": message_id, "reactions": reactions})


async def check_answer(room: Room, ws: WebSocket, name: str, guess: str):
    q = room.current_question()
    if q is None:
        return
    if normalize(guess) != normalize(q["answer"]):
        await room.send_json(ws, {"type": "result", "correct": False})
        return

    room.scores[name] = room.scores.get(name, 0) + q["points"]
    room.current += 1

    await room.send_json(ws, {"type": "result", "correct": True})
    await room.say(f"{name} got it: {q['answer']} (+{q['points']})")
    await room.broadcast_json({"type": "scores", "scores": room.scores})
    await send_question(room)

    if room.current_question() is None:
        await end_round(room)


@router.websocket("")
async def ws_endpoint(
    ws: WebSocket,
    code: str = "",
    create: bool = False,
    deck_id: int = 0,
    count: int = 0,
    max_players: int = 0,
):
    await ws.accept()

    token = ws.cookies.get(SESSION_COOKIE)
    user = user_from_token(token)
    if user is None:
        print(
            f"[trivia] refused a connection: host={ws.headers.get('host')!r} "
            f"origin={ws.headers.get('origin')!r} "
            f"{'no session cookie' if not token else 'session cookie not found or expired'}"
        )
        await ws.close(code=CLOSE_NOT_LOGGED_IN, reason="Log in to play trivia")
        return
    name = (user.Username.strip() or f"Player {user.id}")[:20]

    if create:
        found = load_deck(deck_id, user.id)
        if found is None or not found[1] or not (MIN_PLAYERS <= max_players <= MAX_PLAYERS) or count < 1:
            await ws.close(code=CLOSE_BAD_SETTINGS, reason="Pick a deck, questions and players")
            return
        title, questions = found
        room = manager.create(
            host=name,
            host_user_id=user.id,
            deck_id=deck_id,
            deck_title=title,
            count=min(count, len(questions)),
            max_players=max_players,
        )
    else:
        room = manager.get(code)
        if room is None:
            await ws.close(code=CLOSE_NO_GAME, reason="No game with that code")
            return
        if room.has_name(name):
            await ws.close(code=CLOSE_NAME_TAKEN, reason="You're already in that game")
            return
        if room.started:
            await ws.close(code=CLOSE_ALREADY_STARTED, reason="That game has already started")
            return
        if room.is_full():
            await ws.close(code=CLOSE_GAME_FULL, reason="That game is full")
            return

    await manager.join(room, ws, name)
    is_host = name == room.host

    try:
        while True:
            message = await ws.receive_json()
            if ws not in room.clients:
                break
            kind = message.get("type")

            if kind == "chat":
                text = str(message.get("text", "")).strip()
                if text:
                    await room.chat(name, text[:500])
            elif kind == "react":
                await react(room, name, message.get("id"), message.get("emoji"))
            elif kind == "answer" and room.started:
                await check_answer(room, ws, name, str(message.get("text", "")))

            elif not is_host:
                continue
            elif kind == "next" and room.started:
                await skip_question(room, name)
            elif kind == "start" and not room.started:
                await start_round(room)
            elif kind == "again" and room.started:
                await start_round(room)
            elif kind == "kick":
                await manager.kick(room, str(message.get("name", "")))
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass
    finally:
        await manager.leave(room, ws)
