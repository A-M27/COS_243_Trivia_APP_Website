import secrets

from fastapi import WebSocket

CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 5

CLOSE_NO_NAME = 4000
CLOSE_NAME_TAKEN = 4001
CLOSE_KICKED = 4002
CLOSE_GAME_ENDED = 4003
CLOSE_NO_GAME = 4004
CLOSE_ALREADY_STARTED = 4005
CLOSE_GAME_FULL = 4006
CLOSE_NOT_LOGGED_IN = 4007
CLOSE_BAD_SETTINGS = 4008

MIN_PLAYERS = 2
MAX_PLAYERS = 10


class Room:
    def __init__(self, code: str, host: str, host_user_id: int,
                 deck_id: int, deck_title: str, count: int, max_players: int):
        self.code = code
        self.host = host
        self.host_user_id = host_user_id

        self.clients: dict[WebSocket, str] = {}

        self.deck_id = deck_id
        self.deck_title = deck_title
        self.count = count
        self.max_players = max_players

        self.started = False
        self.questions: list[dict] = []
        self.current = 0
        self.scores: dict[str, int] = {}
        self.wins: dict[str, int] = {}

        self.next_message_id = 1
        self.reactions: dict[int, dict[str, set[str]]] = {}

    def player_names(self) -> list[str]:
        return list(self.clients.values())

    def is_full(self) -> bool:
        return len(self.clients) >= self.max_players

    def has_name(self, name: str) -> bool:
        return name.lower() in (n.lower() for n in self.player_names())

    def socket_for(self, name: str) -> WebSocket | None:
        for ws, n in self.clients.items():
            if n == name:
                return ws
        return None

    def current_question(self) -> dict | None:
        """The question being asked, or None between rounds."""
        if self.current < len(self.questions):
            return self.questions[self.current]
        return None

    def settings(self) -> dict:
        return {
            "deck_id": self.deck_id,
            "deck_title": self.deck_title,
            "count": self.count,
            "max_players": self.max_players,
        }

    async def broadcast_players(self):
        await self.broadcast_json({"type": "players", "players": self.player_names(), "host": self.host})

    async def broadcast_json(self, data: dict):
        for client in list(self.clients):
            await self.send_json(client, data)

    async def send_json(self, client: WebSocket, data: dict):
        """Send to one player."""
        try:
            await client.send_json(data)
        except Exception:
            self.clients.pop(client, None)

    async def chat(self, name: str, text: str):
        message_id = self.next_message_id
        self.next_message_id += 1
        self.reactions[message_id] = {}
        await self.broadcast_json({"type": "chat", "id": message_id, "name": name, "text": text})

    async def say(self, text: str):
        """Post a chat message from the game itself."""
        await self.chat("Host", text)

    def toggle_reaction(self, message_id: int, emoji: str, name: str) -> dict[str, list[str]] | None:
        message = self.reactions.get(message_id)
        if message is None:
            return None
        people = message.setdefault(emoji, set())
        if name in people:
            people.remove(name)
        else:
            people.add(name)
        if not people:
            del message[emoji]
        return {e: sorted(names) for e, names in message.items()}


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Room] = {}

    def new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            if code not in self.rooms:
                return code

    def create(self, **settings) -> Room:
        room = Room(code=self.new_code(), **settings)
        self.rooms[room.code] = room
        return room

    def get(self, code: str) -> Room | None:
        return self.rooms.get(code.strip().upper())

    async def join(self, room: Room, ws: WebSocket, name: str):
        room.clients[ws] = name
        await room.send_json(ws, {"type": "room", "code": room.code, "host": room.host, "you": name})
        await room.send_json(ws, {"type": "settings", **room.settings()})
        await room.send_json(ws, {"type": "wins", "wins": room.wins})
        await room.broadcast_players()

    async def leave(self, room: Room, ws: WebSocket):
        name = room.clients.pop(ws, None)
        if name is None:
            return
        if name == room.host:
            await self.end(room, f"{room.host} (the host) left, so the game ended.")
        else:
            await room.broadcast_players()
            if room.started:
                await room.say(f"{name} left the game.")

    async def kick(self, room: Room, name: str) -> bool:
        ws = room.socket_for(name)
        if ws is None or name == room.host:
            return False
        room.clients.pop(ws, None)
        try:
            await ws.close(code=CLOSE_KICKED, reason="Removed by the host")
        except Exception:
            pass
        await room.broadcast_players()
        await room.say(f"{name} was removed by the host.")
        return True

    async def end(self, room: Room, reason: str):
        self.rooms.pop(room.code, None)
        for ws in list(room.clients):
            try:
                await ws.close(code=CLOSE_GAME_ENDED, reason=reason[:120])
            except Exception:
                pass
        room.clients.clear()


manager = RoomManager()
