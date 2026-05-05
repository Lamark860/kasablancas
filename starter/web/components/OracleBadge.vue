<script setup lang="ts">
import type { OracleSource } from '~/composables/useApi'

defineProps<{ source: OracleSource }>()
</script>

<template>
  <span class="badge" :title="source.reason_for_expert || source.oracle_name">
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
  border: 1px solid var(--rule);
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
</style>
