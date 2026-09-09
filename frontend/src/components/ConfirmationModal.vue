<script setup>
defineProps({ title: { type: String, default: 'Confirm' }, message: { type: String, default: '' }, show: Boolean });
</script>

<template>
  <div class="overlay" v-if="show">
    <div class="modal">
      <h4>{{ title }}</h4>
      <p>{{ message }}</p>
      <div class="actions">
        <button class="btn-cancel" @click="$emit('cancel')">Cancel</button>
        <button @click="$emit('confirm')">Confirm</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Overlay centers the modal and darkens the page */
.overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.45);
  z-index: 1000;
  padding: 1.25rem;
}

/* Modal card */
.modal {
  background: var(--background, #fff);
  color: var(--text, #111);
  border-radius: 16px;
  padding: 1.25rem 1.25rem;
  width: 100%;
  max-width: 520px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
  transform-origin: center;
  animation: popin .16s ease-out;
  outline: none;
}

/* Small visual hierarchy */
.modal h4 {
  margin: 0.75rem 0 0.75rem 0;
  color: var(--text-default);
}
.modal p {
  margin: 0 0 1rem 0;
  color: var(--text-subtle);
  font-size: 1rem;
  line-height: 1.4;
}
.btn-cancel {
    background: transparent;
    color: var(--text-default);
    border: 1px solid var(--border-subtle);
    font-weight: normal;
}

/* Action buttons row */
.actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
}





/* Accessibility focus */
.btn:focus {
  box-shadow: 0 0 0 3px rgba(37,99,235,0.15);
  outline: none;
}


/* Entrance animation */
@keyframes popin {
  from { transform: scale(.985); opacity: 0; }
  to   { transform: scale(1); opacity: 1; }
}
</style>

