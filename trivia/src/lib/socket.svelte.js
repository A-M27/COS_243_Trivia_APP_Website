
export const conn = $state({
  status: "idle",
  error: "",
  code: "",
  host: "",
  you: "",
  players:  ([]),
  messages:  ([]),
  settings: { deck_id: null, deck_title: "", count: 0, max_players: 0 },
  started: false,
  question:  (null),
  scores:  ({}),
  result: "",
  wins: {},
});

const CLOSE_MESSAGES = {
  4001: "You're already in that game (maybe in another tab).",
  4002: "The host removed you from the game.",
  4004: "There's no game with that code. Check it and try again.",
  4005: "That game has already started.",
  4006: "That game is full.",
  4007: "The game server couldn't see your login. Refresh the page, or log out and back in.",
  4008: "Pick a deck, how many questions, and how many players.",
};

let ws;

function serverAddress() {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const host = location.port === "5173" ? `${location.hostname}:8000` : location.host;
  return `${scheme}://${host}`;
}

export function connect(how) {
  disconnect();

  conn.status = "connecting";
  conn.error = "";
  const params = new URLSearchParams(
    "code" in how
      ? { code: how.code }
      : { create: "true", deck_id: String(how.deck_id), count: String(how.count), max_players: String(how.max_players) },
  );
  ws = new WebSocket(`${serverAddress()}/ws?${params}`);

  ws.onopen = () => {
    conn.status = "open";
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "room") {
      conn.code = message.code;
      conn.host = message.host;
      conn.you = message.you;
    } else if (message.type === "players") {
      conn.players = message.players;
      conn.host = message.host;
    } else if (message.type === "chat") {
      conn.messages.push({ id: message.id, name: message.name, text: message.text, reactions: {} });
    } else if (message.type === "reactions") {
      const chat = conn.messages.find((m) => m.id === message.id);
      if (chat) chat.reactions = message.reactions;
    } else if (message.type === "settings") {
      conn.settings = {
        deck_id: message.deck_id,
        deck_title: message.deck_title,
        count: message.count,
        max_players: message.max_players,
      };
    } else if (message.type === "start") {
      conn.started = true;
    } else if (message.type === "question") {
      conn.question = message.question;
      conn.result = "";
    } else if (message.type === "scores") {
      conn.scores = message.scores;
    } else if (message.type === "result") {
      conn.result = message.correct ? "correct" : "wrong";
    } else if (message.type === "wins") {
      conn.wins = message.wins;
    }
  };

  ws.onclose = (event) => {
    const reason = event.code === 4003 ? event.reason : CLOSE_MESSAGES[event.code];
    reset();
    conn.status = "closed";
    conn.error = reason || "Lost connection to the game server.";
  };
}

export function send(data) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

export function disconnect() {
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = undefined;
  }
  reset();
  conn.status = "idle";
}

function reset() {
  ws = undefined;
  conn.code = "";
  conn.host = "";
  conn.you = "";
  conn.players = [];
  conn.messages = [];
  conn.settings = { deck_id: null, deck_title: "", count: 0, max_players: 0 };
  conn.started = false;
  conn.question = null;
  conn.scores = {};
  conn.result = "";
  conn.wins = {};
}
