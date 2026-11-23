
async function problem(response) {
  const data = await response.json().catch(() => null);
  if (typeof data?.detail === "string") {
    return data.detail;
  }
  return `${response.status} ${response.statusText}`;
}

function shuffled(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function createStore(initial) {
  let state = initial;
  const subscribers = [];

  return {
    get() {
      return state;
    },
    set(changes) {
      state = { ...state, ...changes };
      for (const subscriber of subscribers) {
        subscriber(state);
      }
    },
    subscribe(subscriber) {
      subscribers.push(subscriber);
      subscriber(state);
    },
  };
}




const cardTable = document.querySelector("#cards");
const cardStatus = document.querySelector("#card-status");
const noCards = document.querySelector("#no-cards");

async function deleteCard(cardId, row) {
  const button = row.querySelector("button");
  button.disabled = true;
  cardStatus.textContent = "Deleting…";
  try {
    const response = await fetch(`/api/cards/${cardId}`, { method: "DELETE" });
    if (!response.ok) {
      throw new Error(await problem(response));
    }
    row.remove();
    cardStatus.textContent = "Card deleted.";
    if (cardTable.tBodies[0].rows.length === 0) {
      cardTable.hidden = true;
      noCards.textContent = "No cards to show.";
      noCards.hidden = false;
    }
  } catch (error) {
    cardStatus.textContent = `Couldn't delete that card: ${error.message}`;
    button.disabled = false;
  }
}

for (const form of document.querySelectorAll("form.delete-card")) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    deleteCard(form.dataset.cardId, form.closest("tr"));
  });
}






const studyPage = document.querySelector("#study");

if (studyPage) {
  const deckId = studyPage.dataset.deckId;
  const studyTitle = document.querySelector("#study-title");
  const studyStatus = document.querySelector("#study-status");
  const studyArea = document.querySelector("#study-area");
  const position = document.querySelector("#study-position");
  const cardButton = document.querySelector("#study-card");
  const prevButton = document.querySelector("#study-prev");
  const nextButton = document.querySelector("#study-next");
  const shuffleButton = document.querySelector("#study-shuffle");
  const progress = document.querySelector("#study-progress");
  const score = document.querySelector("#study-score");
  const gotButton = document.querySelector("#study-got");
  const missedButton = document.querySelector("#study-missed");
  const resultsArea = document.querySelector("#study-results");
  const resultsHeading = document.querySelector("#results-heading");
  const resultsScore = document.querySelector("#results-score");
  const reviewHeading = document.querySelector("#results-review-heading");
  const reviewList = document.querySelector("#results-review");
  const reviewButton = document.querySelector("#study-review");
  const restartButton = document.querySelector("#study-restart");

  const study = createStore({
    status: "loading",
    error: "",
    title: "",
    cards: [],
    current: 0,
    showingBack: false,
    results: {},
  });

  function renderHeader(state) {
    const title = state.title === "" ? "Study" : `Study: ${state.title}`;
    studyTitle.textContent = title;
    document.title = `${title} · Flashcards`;
    studyStatus.textContent = statusMessage(state);
    studyArea.hidden = state.status !== "ready";
  }

  function statusMessage(state) {
    if (state.status === "loading") {
      return "Loading…";
    }
    if (state.status === "empty") {
      return "This deck has no cards yet.";
    }
    if (state.status === "error") {
      return `Couldn't load this deck: ${state.error}`;
    }
    return "";
  }

  function renderCard(state) {
    if (state.status !== "ready") {
      return;
    }
    const card = state.cards[state.current];
    cardButton.textContent = state.showingBack ? card.Rear : card.Front;
    cardButton.dataset.side = state.showingBack ? "back" : "front";
    position.textContent = `Card ${state.current + 1} of ${state.cards.length}`;
    prevButton.disabled = state.current === 0;
    nextButton.disabled = state.current === state.cards.length - 1;
    gotButton.disabled = !state.showingBack;
    missedButton.disabled = !state.showingBack;
  }

  function renderProgress(state) {
    if (state.status !== "ready") {
      return;
    }
    if (progress.children.length !== state.cards.length) {
      const items = state.cards.map((card, index) => {
        const dot = document.createElement("button");
        dot.type = "button";
        dot.addEventListener("click", () => goTo(index));

        const item = document.createElement("li");
        item.append(dot);
        return item;
      });
      progress.replaceChildren(...items);
    }

    const dots = progress.querySelectorAll("button");
    dots.forEach((dot, index) => {
      const result = state.results[state.cards[index].id];
      dot.dataset.state = index < state.current ? "past" : "ahead";
      dot.dataset.result = result ?? "none";
      const label = result ? `Card ${index + 1}, ${result}` : `Card ${index + 1}`;
      dot.setAttribute("aria-label", label);
      if (index === state.current) {
        dot.setAttribute("aria-current", "step");
      } else {
        dot.removeAttribute("aria-current");
      }
    });
  }

  study.subscribe(renderHeader);
  study.subscribe(renderCard);
  study.subscribe(renderProgress);

  function goTo(index) {
    study.set({ current: index, showingBack: false });
  }

  function grade(result) {
    const state = study.get();
    const card = state.cards[state.current];
    const isLast = state.current === state.cards.length - 1;

    study.set({
      results: { ...state.results, [card.id]: result },
      current: isLast ? state.current : state.current + 1,
      showingBack: false,
    });
  }

  cardButton.addEventListener("click", () => {
    study.set({ showingBack: !study.get().showingBack });
  });
  prevButton.addEventListener("click", () => goTo(study.get().current - 1));
  nextButton.addEventListener("click", () => goTo(study.get().current + 1));
  shuffleButton.addEventListener("click", () => {
    study.set({ cards: shuffled(study.get().cards), current: 0, showingBack: false });
  });
  gotButton.addEventListener("click", () => grade("got"));
  missedButton.addEventListener("click", () => grade("missed"));

  async function loadStudy() {
    try {
      const [deckResponse, cardsResponse] = await Promise.all([
        fetch(`/api/decks/${deckId}`),
        fetch(`/api/decks/${deckId}/cards`),
      ]);
      if (!deckResponse.ok) {
        throw new Error(await problem(deckResponse));
      }
      if (!cardsResponse.ok) {
        throw new Error(await problem(cardsResponse));
      }
      const deck = await deckResponse.json();
      const cards = await cardsResponse.json();
      study.set({
        title: deck.title,
        cards,
        status: cards.length === 0 ? "empty" : "ready",
      });
    } catch (error) {
      study.set({ status: "error", error: error.message });
    }
  }

  loadStudy();
}






const themeButton = document.querySelector("#theme-toggle");

if (themeButton) {
  const page = document.documentElement;
  const deviceIsDark = window.matchMedia("(prefers-color-scheme: dark)");

  function currentTheme() {
    return page.dataset.theme || (deviceIsDark.matches ? "dark" : "light");
  }

  function showButton() {
    const dark = currentTheme() === "dark";
    const label = dark ? "Switch to light mode" : "Switch to dark mode";
    themeButton.textContent = dark ? "☀" : "☾";
    themeButton.setAttribute("aria-label", label);
    themeButton.title = label;
  }

  themeButton.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    page.dataset.theme = next;
    document.cookie = `theme=${next}; path=/; max-age=31536000; SameSite=Lax`;
    showButton();
  });

  deviceIsDark.addEventListener("change", showButton);
  showButton();
}


for (const toggle of document.querySelectorAll(".password-toggle")) {
  const input = document.getElementById(toggle.getAttribute("aria-controls"));
  if (!input) continue;
  toggle.hidden = false;

  toggle.addEventListener("click", () => {
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    const label = showing ? "Show password" : "Hide password";
    toggle.setAttribute("aria-pressed", String(!showing));
    toggle.setAttribute("aria-label", label);
    toggle.title = label;
    input.focus();
  });
}

for (const form of document.querySelectorAll("form")) {
  form.addEventListener("submit", () => {
    for (const input of form.querySelectorAll(".password-field input")) {
      input.type = "password";
    }
  });
}
