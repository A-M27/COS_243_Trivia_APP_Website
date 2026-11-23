<script>
  import Lobby from "./lib/Lobby.svelte";
  import Game from "./lib/Game.svelte";
  import { conn, connect, disconnect } from "./lib/socket.svelte.js";

  let mode = $state("");

  let account = $state(null);
  let loadError = $state("");
  let deckId = $state("");
  let count = $state(10);
  let maxPlayers = $state(4);
  const PLAYER_CHOICES = [2, 3, 4, 5, 6, 8, 10];

  let deck = $derived(account?.decks.find((d) => d.id === deckId));
  let myDecks = $derived(account?.decks.filter((d) => d.mine) ?? []);
  let publicDecks = $derived(account?.decks.filter((d) => !d.mine) ?? []);
  let sizes = $derived(deck ? [...[5, 10, 20, 30].filter((n) => n < deck.cards), deck.cards] : []);
  let canCreate = $derived(deck !== undefined);

  let code = $state("");
  let cleanCode = $derived(code.trim().toUpperCase());
  let canJoin = $derived(cleanCode.length === 5);

  let screen = $derived(
    conn.status === "idle" || conn.status === "closed"
      ? "home"
      : !conn.code
        ? "connecting"
        : conn.started
          ? "game"
          : "lobby",
  );

  $effect(() => {
    if (mode !== "" && account === null && loadError === "") loadAccount();
  });

  async function loadAccount() {
    try {
      const response = await fetch("/api/trivia/decks");
      if (!response.ok) throw new Error();
      account = await response.json();
    } catch {
      loadError = "Couldn't load your decks. Are you logged in?";
    }
  }

  function focus(el) {
    el.focus();
  }

  function pickDeck(event) {
    deckId = Number(event.target.value);
    const cards = account?.decks.find((d) => d.id === deckId)?.cards ?? 0;
    count = Math.min(10, cards);
  }

  function create(event) {
    event.preventDefault();
    if (canCreate) connect({ deck_id: deckId, count, max_players: maxPlayers });
  }

  function join(event) {
    event.preventDefault();
    if (canJoin) connect({ code: cleanCode });
  }

  function leave() {
    disconnect();
    mode = "";
  }
</script>

{#if screen === "home"}
  {#if mode === ""}
    <section class="trivia-card">
      <h2>Trivia</h2>
      <p class="subtitle">Play a flashcard deck against your friends.</p>
      {#if conn.error}
        <p class="error" role="alert">{conn.error}</p>
      {/if}
      <div class="choices">
        <button type="button" onclick={() => (mode = "create")}>
          <strong>Create a game</strong>
          <span>Pick a deck and get a code to share</span>
        </button>
        <button type="button" class="button-secondary" onclick={() => (mode = "join")}>
          <strong>Join a game</strong>
          <span>Enter the code from your host</span>
        </button>
      </div>
    </section>
  {:else if mode === "create"}
    <form class="trivia-card" onsubmit={create}>
      <h2>Create a game</h2>
      {#if account}
        <p class="subtitle">You'll host as <strong>{account.username}</strong>.</p>
      {/if}
      {#if conn.error || loadError}
        <p class="error" role="alert">{conn.error || loadError}</p>
      {/if}

      <p class="field">
        <label for="deck">Deck</label>
        <select id="deck" value={deckId} onchange={pickDeck} disabled={!account} {@attach focus}>
          <option value="" disabled>{account ? "Choose a deck…" : "Loading decks…"}</option>
          {#if myDecks.length}
            <optgroup label="Your decks">
              {#each myDecks as d (d.id)}
                <option value={d.id}>{d.title} ({d.cards} cards)</option>
              {/each}
            </optgroup>
          {/if}
          {#if publicDecks.length}
            <optgroup label="Public decks">
              {#each publicDecks as d (d.id)}
                <option value={d.id}>{d.title} ({d.cards} cards)</option>
              {/each}
            </optgroup>
          {/if}
        </select>
        {#if account && account.decks.length === 0}
          <span class="help">There are no decks with cards to play yet. <a href="/decks/new">Make one</a>.</span>
        {:else}
          <span class="help">The deck's title becomes the name of the game.</span>
        {/if}
      </p>

      <p class="field">
        <label for="count">How many questions</label>
        <select id="count" bind:value={count} disabled={!deck}>
          {#if !deck}
            <option value={count}>Choose a deck first</option>
          {/if}
          {#each sizes as n (n)}
            <option value={n}>{n === deck?.cards ? `All ${n}` : n}</option>
          {/each}
        </select>
      </p>

      <p class="field">
        <label for="players">How many players</label>
        <select id="players" bind:value={maxPlayers}>
          {#each PLAYER_CHOICES as n (n)}
            <option value={n}>{n} players</option>
          {/each}
        </select>
        <span class="help">Including you. Nobody else can join once it's full.</span>
      </p>

      <div class="actions">
        <button disabled={!canCreate}>Create game</button>
        <button type="button" class="button-secondary" onclick={() => (mode = "")}>Back</button>
      </div>
    </form>
  {:else}
    <form class="trivia-card" onsubmit={join}>
      <h2>Join a game</h2>
      {#if account}
        <p class="subtitle">You'll play as <strong>{account.username}</strong>.</p>
      {/if}
      {#if conn.error}
        <p class="error" role="alert">{conn.error}</p>
      {/if}

      <p class="field">
        <label for="code">Game code</label>
        <input id="code" class="code" bind:value={code} maxlength="5" autocomplete="off" placeholder="e.g. K7QXM" {@attach focus} />
        <span class="help">The 5-character code from the person hosting.</span>
      </p>

      <div class="actions">
        <button disabled={!canJoin}>Join game</button>
        <button type="button" class="button-secondary" onclick={() => (mode = "")}>Back</button>
      </div>
    </form>
  {/if}
{:else if screen === "connecting"}
  <section class="trivia-card">
    <p>Connecting to the game server…</p>
  </section>
{:else if screen === "lobby"}
  <Lobby onleave={leave} />
{:else}
  <Game ondone={leave} />
{/if}

<style>
  .choices {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .choices button {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-1);
    padding: var(--space-3) var(--space-4);
    text-align: left;
  }

  .choices span {
    font-size: var(--text-sm);
    opacity: 0.85;
  }

  .code {
    text-transform: uppercase;
    letter-spacing: 0.2em;
  }

  .error {
    padding: var(--space-2) var(--space-3);
    background: var(--color-accent-soft);
    border-left: 4px solid var(--color-error);
    border-radius: var(--radius);
  }
</style>
