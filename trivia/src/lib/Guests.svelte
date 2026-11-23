<script>
  import GuestList from "./GuestList.svelte";
  let guests = $state([]);
  let draft = $state("");
  let nextId = 1;

  function add(event) {
    event.preventDefault();
    const name = draft.trim();
    if (name === "") {
      return;
    }
    guests.push({ id: nextId, name });
    nextId += 1;
    draft = "";
  }

  function remove(id) {
    guests = guests.filter((guest) => guest.id !== id);
  }
</script>

<form onsubmit={add}>
  <p>
    <label for="guest">Guest</label>
    <input id="guest" bind:value={draft} />
  </p>
  <button>Add</button>
</form>

<GuestList {guests} onremove={remove} />
