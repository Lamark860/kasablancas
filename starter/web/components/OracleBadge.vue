<script setup lang="ts">
import type { OracleSource } from '~/composables/useApi'

defineProps<{ source: OracleSource }>()
</script>

<template>
  <span
    class="badge"
    :class="`badge--${source.oracle_id}`"
    :title="source.reason_for_expert || source.oracle_name"
  >
    <span class="badge__name">{{ source.oracle_name }}</span>
    <span v-if="source.weight !== 1" class="badge__weight">×{{ source.weight }}</span>
  </span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 3px 8px;
  background: var(--paper-deep);
  border: 1px solid currentColor;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  cursor: help;
}
.badge__weight {
  color: var(--ink-faded);
  font-size: 8px;
  letter-spacing: 0;
}

/* Цветовая карта оракулов (спека дизайнера Prototype v2). */
.badge--druid_tree   { color: #4a6b3c; border-color: #6b8e5a; }
.badge--druid_flower { color: #944f6b; border-color: #c97c9b; }
.badge--zodiac       { color: #614a82; border-color: #9170b8; }
.badge--numerology   { color: #7a5e22; border-color: #b08d44; }
.badge--eye_color    { color: #3d6580; border-color: #5d8aa8; }
.badge--name         { color: #8b5a2a; border-color: #c08552; }
.badge--slavic       { color: #7a3520; border-color: #a64b2a; }
.badge--lunar        { color: #4a4a82; border-color: #7070b8; }
</style>
