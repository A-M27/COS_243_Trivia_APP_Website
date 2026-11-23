<script>
  import { conn, send } from "./socket.svelte.js";
  import Players from "./Players.svelte";

  let { onleave } = $props();

  let isHost = $derived(conn.you === conn.host);
  let seatsLeft = $derived(conn.settings.max_players - conn.players.length);

  function kick(name) {
    send({ type: "kick", name });
  }
</script>

<section class="trivia-card">
  <h2>{conn.settings.deck_title || "Trivia"}</h2>
  <p class="subtitle">
    {conn.settings.count} questions · up to {conn.settings.max_players} players · hosted by {conn.host}
  </p>

  <div class="code-box">
    <span>{isHost ? "Share this code with your players" : "Game code"}</span>
    <strong class="code">{conn.code}</strong>
  </div>

  <div class="players">
    <h3>Players ({conn.players.length} of {conn.settings.max_players})</h3>
    <Players
      players={conn.players.map((name) => ({ name }))}
      host={conn.host}
      you={conn.you}
      wins={conn.wins}
      onkick={isHost ? kick : undefined}
    />
    <span class="help">
      {#if seatsLeft > 0}
        Waiting for players: {seatsLeft} {seatsLeft === 1 ? "spot" : "spots"} left.
      {:else}
        The game is full.
      {/if}
      {#if !isHost}{conn.host} will start the game.{/if}
    </span>
  </div>

  <div class="actions">
    {#if isHost}
      <button type="button" onclick={() => send({ type: "start" })}>Start game</button>
    {/if}
    <button type="button" class="button-secondary" onclick={onleave}>{isHost ? "Cancel game" : "Leave"}</button>
  </div>
</section>

<style>
  .code-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-4);
    background: var(--color-accent-soft);
    border-radius: var(--radius-lg);
  }

  .code-box span,
  .help {
    font-size: var(--text-sm);
    color: var(--color-muted);
  }

  .code {
    font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
    font-size: var(--text-xl);
    letter-spacing: 0.25em;
    color: var(--color-accent);
  }

  .players {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .players h3 {
    margin: 0;
    font-size: var(--text-base);
  }
</style>
