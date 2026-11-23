<script>
  import { conn, send } from "./socket.svelte.js";
  import Players from "./Players.svelte";

  let { ondone } = $props();

  const REACTIONS = ["👍", "😂", "🔥", "🎉", "🤯"];

  let message = $state("");
  let guess = $state("");
  let chatBox;

  let isHost = $derived(conn.you === conn.host);

  function kick(name) {
    send({ type: "kick", name });
  }

  let board = $derived.by(() => {
    const rows = conn.players
      .map((name) => ({ name, score: conn.scores[name] ?? 0 }))
      .sort((a, b) => b.score - a.score);
    return rows.map((row) => ({ ...row, rank: 1 + rows.filter((r) => r.score > row.score).length }));
  });

  let me = $derived(board.find((p) => p.name === conn.you));
  let leader = $derived(board[0]);
  let pointsBehind = $derived(leader && me ? leader.score - me.score : 0);
  let percent = $derived(conn.question ? Math.round(((conn.question.number - 1) / conn.question.total) * 100) : 100);
  let winners = $derived(leader?.score > 0 ? board.filter((p) => p.score === leader.score).map((p) => p.name) : []);

  $effect(() => {
    conn.messages.length;
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
  });

  function sendMessage(event) {
    event.preventDefault();
    const text = message.trim();
    if (!text) return;
    send({ type: "chat", text });
    message = "";
  }

  function submitAnswer(event) {
    event.preventDefault();
    const text = guess.trim();
    if (!text) return;
    send({ type: "answer", text });
    guess = "";
  }
</script>

<section class="game">
  <p class="meta">
    <strong>{conn.settings.deck_title}</strong> · game {conn.code}
    {#if me}
      · You're {me.rank === 1 && me.score > 0 ? "in the lead" : `#${me.rank}`} with {me.score} pts
      {#if pointsBehind > 0}({pointsBehind} behind {leader.name}){/if}
    {/if}
  </p>

  <div class="progress" role="progressbar" aria-label="Deck progress" aria-valuenow={percent}>
    <div style:width="{percent}%"></div>
  </div>

  {#if conn.question}
    <p class="meta">Question {conn.question.number} of {conn.question.total} · {conn.question.points} pts</p>
    <p class="question">{conn.question.text}</p>

    <form class="row" onsubmit={submitAnswer}>
      <label for="guess">Your answer:</label>
      <input id="guess" bind:value={guess} autocomplete="off" />
      <button>Answer</button>
    </form>

    {#if conn.result}
      <p class="result" data-result={conn.result}>
        {conn.result === "correct" ? "Correct!" : "Not quite. Try again."}
      </p>
    {/if}

    {#if isHost}
      <button class="button-secondary" onclick={() => send({ type: "next" })}>Skip question</button>
    {/if}
  {:else}
    <div class="round-over">
      <p class="question">
        Round over! {winners.length === 0
          ? "Nobody scored."
          : winners.length === 1
            ? `${winners[0]} wins 👑`
            : `It's a tie: ${winners.join(" & ")} 👑`}
      </p>
      <div class="row">
        <a href="/decks/{conn.settings.deck_id}/study">Study {conn.settings.deck_title}</a>
        {#if isHost}
          <button onclick={() => send({ type: "again" })}>Play again</button>
        {:else}
          <span class="meta">Waiting for {conn.host} to start the next round…</span>
        {/if}
      </div>
    </div>
  {/if}

  <div class="table">
    <div class="chat" bind:this={chatBox}>
      {#if conn.messages.length === 0}
        <p class="meta">No messages yet.</p>
      {:else}
        <ul>
          {#each conn.messages as m (m.id)}
            <li>
              <strong>{m.name}:</strong>
              {m.text}
              <span class="reactions">
                {#each REACTIONS as emoji (emoji)}
                  {@const names = m.reactions[emoji] ?? []}
                  <button
                    type="button"
                    class:on={names.includes(conn.you)}
                    class:used={names.length > 0}
                    title={names.join(", ") || `React with ${emoji}`}
                    onclick={() => send({ type: "react", id: m.id, emoji })}
                  >
                    {emoji}{names.length ? ` ${names.length}` : ""}
                  </button>
                {/each}
              </span>
            </li>
          {/each}
        </ul>
      {/if}
    </div>

    <div class="board">
      <Players
        players={board}
        host={conn.host}
        you={conn.you}
        wins={conn.wins}
        onkick={isHost ? kick : undefined}
      />
    </div>
  </div>

  <form class="row" onsubmit={sendMessage}>
    <label for="message">Send a message:</label>
    <input id="message" bind:value={message} autocomplete="off" />
    <button>Send</button>
  </form>

  <button class="button-secondary" onclick={ondone}>{isHost ? "End game for everyone" : "Leave game"}</button>
</section>

<style>
  .game {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
    max-width: var(--width-study);
    margin: var(--space-4) auto;
    padding: var(--space-5);
    background: var(--color-surface);
    border: 2px solid var(--color-accent);
    border-radius: var(--radius-lg);
  }

  .game p {
    margin: 0;
  }

  .meta {
    color: var(--color-muted);
  }

  .question {
    font-size: var(--text-card);
    white-space: pre-wrap;
  }

  .row {
    align-self: stretch;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
  }

  .row label {
    flex: none;
    font-weight: 600;
  }

  .row input {
    flex: 1 1 12rem;
  }

  .progress {
    align-self: stretch;
    height: 0.5rem;
    background: var(--color-accent-soft);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress div {
    height: 100%;
    background: var(--color-accent);
    transition: width 0.4s ease;
  }

  .round-over {
    align-self: stretch;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    padding: var(--space-4);
    background: var(--color-accent-soft);
    border-radius: var(--radius-lg);
  }

  .table {
    align-self: stretch;
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .board {
    flex: 1 1 12rem;
  }

  .chat {
    flex: 3 1 16rem;
    max-height: 16rem;
    min-height: 16rem;
    overflow-y: auto;
    padding: var(--space-3);
    border: 1px solid var(--color-muted);
    border-radius: var(--radius-lg);
  }

  .chat ul {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .reactions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1);
  }

  .reactions button {
    --button-bg: transparent;
    --button-bg-hover: var(--color-accent-soft);
    --button-text: var(--color-text);
    min-height: 0;
    padding: 0 var(--space-2);
    font-size: var(--text-sm);
    border: 1px solid var(--color-border);
    border-radius: 999px;
    opacity: 0.35;
  }

  li:hover .reactions button,
  .reactions button.used,
  .reactions button:focus-visible {
    opacity: 1;
  }

  .reactions button.on {
    --button-bg: var(--color-accent-soft);
    border-color: var(--color-accent);
  }

  .result[data-result="correct"] {
    color: var(--color-correct);
    font-weight: 600;
  }

  .result[data-result="wrong"] {
    color: var(--color-error);
  }
</style>
