<script>
  let { guests, onremove } = $props();
</script>

<ul>
  {#each guests as guest (guest.id)}
    <li>
      {guest.name}
      <button type="button" onclick={() => onremove(guest.id)}>Remove</button>
    </li>
  {:else}
    <li>No guests yet.</li>
  {/each}
</ul>
<p>{guests.length} {guests.length === 1 ? "guest" : "guests"}</p>
