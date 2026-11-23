<script>
  let { players, host, you, wins = {}, onkick = undefined } = $props();

  const places = ["1st", "2nd", "3rd"];
</script>

<ol class="players">
  {#each players as p (p.name)}
    <li data-rank={p.score > 0 ? p.rank : ""}>
      {#if p.rank}
        <span class="rank">{places[p.rank - 1] ?? `${p.rank}th`}</span>
      {/if}
      <span class="who">
        <span>
          {p.name}
          {#if p.name === host}<span class="tag">host</span>{/if}
          {#if p.name === you}<span class="tag">you</span>{/if}
        </span>
        {#if wins[p.name]}
          <span class="crowns" title="{wins[p.name]} rounds won">{"👑".repeat(wins[p.name])}</span>
        {/if}
      </span>
      {#if p.score !== undefined}
        <strong>{p.score}</strong>
      {/if}
      {#if onkick && p.name !== host}
        <button type="button" class="kick" onclick={() => onkick(p.name)}>Remove</button>
      {/if}
    </li>
  {/each}
</ol>

<style>
  .players {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  li {
    --rank-color: var(--color-border);
    display: flex;
    align-items: center;
    gap: var(--space-3);
    min-height: var(--tap);
    padding: var(--space-1) var(--space-3);
    background: var(--color-surface);
    border: 2px solid var(--rank-color);
    border-radius: var(--radius);
  }

  li[data-rank="1"] {
    --rank-color: var(--color-gold);
  }
  li[data-rank="2"] {
    --rank-color: var(--color-silver);
  }
  li[data-rank="3"] {
    --rank-color: var(--color-bronze);
  }

  .rank {
    flex: 0 0 2.75rem;
    text-align: center;
    font-size: var(--text-sm);
    font-weight: 700;
    border-radius: 999px;
    background: var(--rank-color);
  }

  .who {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow-wrap: anywhere;
  }

  .crowns {
    font-size: var(--text-sm);
  }

  .tag {
    margin-left: var(--space-1);
    padding: 0 var(--space-2);
    font-size: var(--text-sm);
    color: var(--color-accent);
    background: var(--color-accent-soft);
    border-radius: 999px;
  }

  .kick {
    --button-bg: transparent;
    --button-bg-hover: var(--color-accent-soft);
    --button-text: var(--color-error);
    min-height: 2rem;
    padding: 0 var(--space-3);
    font-size: var(--text-sm);
    border-color: var(--color-error);
  }
</style>
