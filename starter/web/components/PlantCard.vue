<script setup lang="ts">
import type { PoolEntry } from '~/composables/useApi'

const props = defineProps<{
  entry: PoolEntry
  index: number
  curatable?: boolean
  curated?: boolean
  isTitle?: boolean
  curatedNote?: string | null
  /** «новая» — при снятом фильтре карточка из ранее исключённых; золотая рамка. */
  isNew?: boolean
  /** Причина зимовки (например «min USDA 6 > участка 5»); рисует маркер ❋. */
  frostReason?: string | null
}>()

const emit = defineEmits<{
  (e: 'toggle-curated', slug: string): void
  (e: 'set-title', slug: string): void
  (e: 'update-note', slug: string, note: string): void
}>()

function onNoteInput(ev: Event) {
  emit('update-note', props.entry.plant_slug, (ev.target as HTMLTextAreaElement).value)
}

const weightFmt = computed(() => props.entry.total_weight.toFixed(1))
const diamonds = computed(() => '◆'.repeat(Math.min(props.entry.match_count, 6)))
const shortName = computed(() => {
  const n = props.entry.plant_name_ru || props.entry.plant_slug
  return n.length > 4 ? n.slice(0, 4).toLowerCase() : n.toLowerCase()
})
</script>

<template>
  <article
    class="plant-card"
    :class="{
      'plant-card--curated': curated,
      'plant-card--title': isTitle,
      'plant-card--new': isNew,
    }"
  >
    <div v-if="isTitle" class="plant-card__princeps">arbor princeps</div>
    <div v-if="isNew" class="plant-card__new-badge">+ за пределами зоны</div>

    <!-- Левая колонка: инициал-монограмма -->
    <div class="plant-card__mono" aria-hidden="true">{{ shortName }}</div>

    <!-- Центральная колонка: имя + оракулы + причины -->
    <div class="plant-card__body">
      <header class="plant-card__head">
        <span
          v-if="frostReason"
          class="plant-card__frost"
          :title="`не зимует — ${frostReason}`"
        >❋</span>
        <h3 class="plant-card__name">{{ entry.plant_name_ru || entry.plant_slug }}</h3>
        <span class="plant-card__lat">{{ entry.plant_slug }}</span>
      </header>

      <div class="plant-card__meta">
        <strong>{{ entry.match_count }}</strong> {{ entry.match_count === 1 ? 'оракул' : 'оракула' }}
        <span class="plant-card__sep">·</span>
        мин. зона <strong>?</strong>
      </div>

      <div class="plant-card__tags">
        <OracleBadge v-for="src in entry.sources" :key="src.oracle_id" :source="src" />
      </div>

      <ul v-if="entry.sources.length" class="plant-card__reasons">
        <li v-for="src in entry.sources" :key="`r-${src.oracle_id}`">
          <em>{{ src.oracle_name }}.</em>
          <span class="plant-card__reason-text">{{ src.reason_for_expert || '—' }}</span>
        </li>
      </ul>

      <ul v-if="entry.notes.length" class="plant-card__notes">
        <li v-for="(n, i) in entry.notes" :key="i">{{ n }}</li>
      </ul>

      <!-- Note-блок: появляется ТОЛЬКО при curated. Внутри textarea + кнопка «главное» -->
      <div v-if="curatable && curated" class="plant-card__note-block">
        <div class="plant-card__note-label">
          note expert <span v-if="isTitle"> · главное дерево</span>
        </div>
        <textarea
          class="plant-card__note-area"
          rows="2"
          :value="curatedNote || ''"
          placeholder="заметка эксперта для отчёта…"
          @input="onNoteInput"
        />
        <button
          v-if="!isTitle"
          type="button"
          class="plant-card__title-btn"
          @click="emit('set-title', entry.plant_slug)"
        >✦ отметить главным</button>
        <span v-else class="plant-card__title-mark">✦ главное дерево</span>
      </div>
    </div>

    <!-- Правая колонка: ромбы + вес + кнопка в коллекцию -->
    <aside class="plant-card__score">
      <div class="plant-card__diamonds">{{ diamonds }}</div>
      <div class="plant-card__weight" :title="`total_weight = ${entry.total_weight}`">
        вес <strong>{{ weightFmt }}</strong>
      </div>
      <button
        v-if="curatable"
        type="button"
        class="plant-card__collect"
        :class="{ 'plant-card__collect--in': curated }"
        @click="emit('toggle-curated', entry.plant_slug)"
      >
        {{ curated ? '✓ в коллекции' : '+ в коллекцию' }}
      </button>
    </aside>
  </article>
</template>

<style scoped>
.plant-card {
  display: grid;
  grid-template-columns: 56px 1fr 130px;
  gap: 18px;
  padding: 16px;
  margin: 10px 0;
  border: 1px solid var(--rule);
  background: var(--paper);
  position: relative;
}

.plant-card__mono {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--paper-deep);
  border: 1px solid var(--rule);
  font-family: var(--display);
  font-size: 18px;
  color: var(--ink);
  letter-spacing: 0.04em;
}

.plant-card__head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}
.plant-card__name {
  font-family: var(--display);
  font-weight: 400;
  font-size: 24px;
  line-height: 1;
  margin: 0;
  color: var(--ink);
}
.plant-card__lat {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}
.plant-card__frost {
  color: var(--gold, #b08d44);
  font-size: 14px;
  cursor: help;
}

.plant-card__meta {
  font-family: var(--serif);
  font-size: 13px;
  font-style: italic;
  color: var(--ink-faded);
  margin-top: 4px;
}
.plant-card__meta strong { font-style: normal; color: var(--ink); }
.plant-card__sep { color: var(--rule); margin: 0 4px; }

.plant-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 8px 0 8px;
}

.plant-card__reasons {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
}
.plant-card__reasons li {
  font-family: var(--serif);
  font-size: 13px;
  line-height: 1.45;
  color: var(--ink-soft);
  padding-left: 14px;
  position: relative;
}
.plant-card__reasons li::before {
  content: '—';
  position: absolute;
  left: 0;
  color: var(--terra);
}
.plant-card__reasons em {
  color: var(--ink);
  font-style: italic;
  margin-right: 4px;
}
.plant-card__reason-text { color: var(--ink-faded); }

.plant-card__notes {
  list-style: none;
  margin: 8px 0 0;
  padding: 6px 10px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-soft);
}

/* Note-блок — только при curated */
.plant-card__note-block {
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
}
.plant-card__note-label {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 4px;
}
.plant-card__note-area {
  width: 100%;
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--rule);
  padding: 6px 8px;
  resize: vertical;
  outline: none;
  display: block;
}
.plant-card__note-area:focus { border-color: var(--terra); }
.plant-card__title-btn {
  margin-top: 8px;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  background: transparent;
  border: 1px dashed var(--terra);
  padding: 5px 10px;
  cursor: pointer;
}
.plant-card__title-btn:hover { background: var(--terra); color: var(--paper); }
.plant-card__title-mark {
  display: inline-block;
  margin-top: 8px;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
}

/* Правая колонка — ромбы, вес, кнопка */
.plant-card__score {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}
.plant-card__diamonds {
  color: var(--terra);
  font-size: 16px;
  letter-spacing: 2px;
  line-height: 1;
}
.plant-card__weight {
  font-family: var(--serif);
  font-style: italic;
  font-size: 12px;
  color: var(--ink-faded);
}
.plant-card__weight strong { font-style: normal; color: var(--ink); }
.plant-card__collect {
  margin-top: auto;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--rule);
  padding: 6px 10px;
  cursor: pointer;
  white-space: nowrap;
}
.plant-card__collect:hover { border-color: var(--ink); }
.plant-card__collect--in {
  color: var(--terra);
  border-color: var(--terra);
}
.plant-card__collect--in:hover { background: var(--terra); color: var(--paper); }

.plant-card--curated {
  background: var(--paper-deep);
}
.plant-card--title {
  border: 1.5px solid var(--terra);
}
.plant-card__princeps {
  position: absolute;
  top: -10px;
  left: 16px;
  padding: 1px 8px;
  background: var(--terra);
  color: var(--paper);
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
}

.plant-card--new {
  box-shadow: 0 0 0 2px var(--gold-soft, #d4b876);
}
.plant-card__new-badge {
  position: absolute;
  top: -10px;
  right: 16px;
  padding: 1px 8px;
  background: var(--gold, #b08d44);
  color: var(--paper);
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
}
</style>
