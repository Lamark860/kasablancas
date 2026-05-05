<script setup lang="ts">
import type { PoolEntry } from '~/composables/useApi'

const props = defineProps<{
  entry: PoolEntry
  index: number
  curatable?: boolean
  curated?: boolean
  isTitle?: boolean
  curatedNote?: string | null
}>()

const emit = defineEmits<{
  (e: 'toggle-curated', slug: string): void
  (e: 'set-title', slug: string): void
  (e: 'update-note', slug: string, note: string): void
}>()

function onNoteInput(ev: Event) {
  emit('update-note', props.entry.plant_slug, (ev.target as HTMLTextAreaElement).value)
}

const numLabel = computed(() => String(props.index + 1).padStart(2, '0'))
const weightFmt = computed(() => props.entry.total_weight.toFixed(2))
</script>

<template>
  <article class="plant-card" :class="{ 'plant-card--curated': curated, 'plant-card--title': isTitle }">
    <div class="plant-card__icon" aria-hidden="true">
      <svg viewBox="0 0 56 56" width="48" height="48">
        <circle cx="28" cy="28" r="22" fill="none" stroke="currentColor" stroke-width="1" />
        <path d="M28 50 L 28 24 M 28 32 C 22 30 18 26 20 22 M 28 32 C 34 30 38 26 36 22" fill="none" stroke="currentColor" stroke-width="0.9" stroke-linecap="round" />
      </svg>
    </div>

    <div class="plant-card__body">
      <header class="plant-card__head">
        <span class="plant-card__num">{{ numLabel }}</span>
        <span class="plant-card__name">{{ entry.plant_name_ru || entry.plant_slug }}</span>
        <span class="plant-card__slug">{{ entry.plant_slug }}</span>
      </header>

      <div class="plant-card__sources">
        <OracleBadge v-for="src in entry.sources" :key="src.oracle_id" :source="src" />
      </div>

      <p v-if="entry.plant_short_story" class="plant-card__story">
        {{ entry.plant_short_story }}
      </p>

      <ul v-if="entry.sources.length" class="plant-card__reasons">
        <li v-for="src in entry.sources" :key="`r-${src.oracle_id}`">
          <em>{{ src.oracle_name }}.</em>
          <span class="plant-card__reason-text">{{ src.reason_for_expert || '—' }}</span>
        </li>
      </ul>

      <ul v-if="entry.notes.length" class="plant-card__notes">
        <li v-for="(n, i) in entry.notes" :key="i">{{ n }}</li>
      </ul>
    </div>

    <aside class="plant-card__score">
      <div class="plant-card__stars" aria-hidden="true">
        <span v-for="i in entry.match_count" :key="i">✦</span>
      </div>
      <div class="plant-card__count">{{ entry.match_count }}</div>
      <div class="plant-card__count-label">пересеч.</div>
      <div class="plant-card__weight" :title="`total_weight = ${entry.total_weight}`">
        вес <strong>{{ weightFmt }}</strong>
      </div>

      <div v-if="curatable" class="plant-card__curate">
        <label class="plant-card__check">
          <input
            type="checkbox"
            :checked="curated"
            @change="emit('toggle-curated', entry.plant_slug)"
          />
          <span>в избранное</span>
        </label>
        <label class="plant-card__check" :class="{ 'plant-card__check--disabled': !curated }">
          <input
            type="radio"
            name="title-plant"
            :checked="isTitle"
            :disabled="!curated"
            @change="emit('set-title', entry.plant_slug)"
          />
          <span>главное</span>
        </label>
      </div>
    </aside>

    <div v-if="curatable && curated" class="plant-card__per-note">
      <label>
        <span class="plant-card__per-note-label">заметка эксперта на это растение</span>
        <textarea
          class="plant-card__per-note-area"
          rows="2"
          :value="curatedNote || ''"
          placeholder="например: ставить ближе к воде, не на холм"
          @input="onNoteInput"
        />
      </label>
    </div>
  </article>
</template>

<style scoped>
.plant-card {
  display: grid;
  grid-template-columns: 70px 1fr 90px;
  gap: 16px;
  padding: 18px 0;
  border-bottom: 1px solid var(--rule);
  align-items: flex-start;
}
.plant-card:last-child { border-bottom: none; }

.plant-card__icon {
  width: 70px;
  height: 70px;
  background: var(--paper-deep);
  border: 1px solid var(--rule);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink);
}

.plant-card__head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}
.plant-card__num {
  font-family: var(--sans);
  font-size: 14px;
  color: var(--terra);
}
.plant-card__name {
  font-family: var(--display);
  font-size: 22px;
  line-height: 1;
  color: var(--ink);
}
.plant-card__slug {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}

.plant-card__sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0 8px;
}

.plant-card__story {
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  line-height: 1.5;
  color: var(--ink-soft);
  margin: 8px 0 0;
  max-width: 56ch;
}

.plant-card__reasons {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
}
.plant-card__reasons li {
  font-family: var(--serif);
  font-size: 14px;
  line-height: 1.5;
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
  font-size: 14px;
  color: var(--ink-soft);
}

.plant-card__score {
  text-align: right;
}
.plant-card__stars {
  color: var(--terra);
  font-family: var(--display);
  font-size: 16px;
  letter-spacing: 1px;
}
.plant-card__count {
  font-family: var(--display);
  font-size: 36px;
  color: var(--ink);
  margin-top: 4px;
}
.plant-card__count-label {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faded);
  margin-top: 2px;
}
.plant-card__weight {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 8px;
}
.plant-card__weight strong {
  font-style: normal;
  color: var(--ink);
}

.plant-card--curated {
  background: var(--paper-deep);
  margin: 0 -10px;
  padding: 18px 10px;
}
.plant-card--title {
  border-left: 3px solid var(--terra);
  padding-left: 10px;
}

.plant-card__curate {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}
.plant-card__check {
  display: flex;
  gap: 6px;
  align-items: center;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  cursor: pointer;
  white-space: nowrap;
}
.plant-card__check--disabled { color: var(--ink-faded); cursor: not-allowed; }
.plant-card__check input { cursor: inherit; }

.plant-card__per-note {
  grid-column: 2 / span 2;
  margin-top: 4px;
}
.plant-card__per-note-label {
  display: block;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 4px;
}
.plant-card__per-note-area {
  width: 100%;
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink);
  background: var(--paper-deep);
  border: 1px solid var(--rule);
  padding: 6px 8px;
  resize: vertical;
  outline: none;
}
.plant-card__per-note-area:focus { border-color: var(--terra); }
</style>
