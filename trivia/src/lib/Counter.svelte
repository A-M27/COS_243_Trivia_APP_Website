<script>
  let count = $state(0);
  let doubled = $derived(count * 2);
  let isBig = $derived(count >= 10);

  $effect(() => {
    document.title = `Count: ${count}`;
  });
</script>

<p>{count} doubled is {doubled}</p>
<button onclick={() => (count += 1)}>Add one</button>
<button onclick={() => (count = 0)} disabled={count === 0}>Reset</button>

{#if isBig}
  <p>That's a big number.</p>
{/if}
