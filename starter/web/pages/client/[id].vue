<script setup lang="ts">
import type { Person, RecommendationOut, PoolEntry } from '~/composables/useApi'

const route = useRoute()
const api = useApi()

const personId = computed(() => Number(route.params.id))

const { data: person, error: personError } = await useAsyncData<Person>(
  () => `person-${personId.value}`,
  () => api.getPerson(personId.value),
  { watch: [personId] },
)

const { data: rec, error: recError } = await useAsyncData<RecommendationOut>(
  () => `curated-${personId.value}`,
  () => api.getCurated(personId.value),
  { watch: [personId] },
)

interface ClientItem {
  slug: string
  name_ru: string
  short_story: string | null
  expert_note: string | null
}

function pick(slug: string, expert_note: string | null): ClientItem {
  const raw: PoolEntry | undefined = rec.value?.raw_pool.find((p) => p.plant_slug === slug)
  return {
    slug,
    name_ru: raw?.plant_name_ru || slug,
    short_story: raw?.plant_short_story ?? null,
    expert_note,
  }
}

const main = computed<ClientItem | null>(() => {
  if (!rec.value || !rec.value.curated_pool?.length) return null
  const items = rec.value.curated_pool
  const titleSlug = rec.value.title_plant_slug || items[0].plant_slug
  const titleItem = items.find((it) => it.plant_slug === titleSlug) ?? items[0]
  return pick(titleItem.plant_slug, titleItem.expert_note ?? null)
})

const others = computed<ClientItem[]>(() => {
  if (!rec.value || !main.value) return []
  return (rec.value.curated_pool || [])
    .filter((it) => it.plant_slug !== main.value!.slug)
    .map((it) => pick(it.plant_slug, it.expert_note ?? null))
})

const firstName = computed(() => person.value?.first_name || 'госпожа')
const pdfUrl = computed(() => api.reportPdfUrl(personId.value))

const notSaved = computed(() => recError.value && (recError.value as any)?.statusCode === 404)
</script>

<template>
  <main class="v-page v-page--narrow client-page">
    <div class="v-sheet v-grain client-sheet">
      <div class="v-frame">
        <header class="masthead">
          <div class="symbols" aria-hidden="true">☉ ✦ ☾</div>
          <h1 class="title">Hortus Animæ</h1>
          <div class="sub">персональный лист растений</div>
        </header>

        <div v-if="personError" class="error">гостья #{{ personId }} не найдена</div>

        <div v-else-if="notSaved" class="error">
          лист ещё не свёрстан.
          <NuxtLink :to="`/expert/${personId}`">вернуться к экспертному</NuxtLink>
          и нажать «сохранить».
        </div>

        <template v-else-if="rec && person">
          <div class="for">
            <div class="for__label">составлено для</div>
            <div class="for__name">{{ firstName }}</div>
          </div>

          <section v-if="main" class="main-tree">
            <div class="main-tree__eyebrow">главное дерево</div>
            <div class="icon-circle" aria-hidden="true">
              <span class="icon-circle__letter">{{ main.name_ru[0] }}</span>
            </div>
            <h2 class="main-tree__name">{{ main.name_ru }}</h2>
            <p v-if="main.short_story" class="main-tree__story">«{{ main.short_story }}»</p>
            <p v-if="main.expert_note" class="main-tree__note">{{ main.expert_note }}</p>
          </section>

          <section v-if="others.length" class="others">
            <div class="others__eyebrow">сопровождают</div>
            <div class="others__grid">
              <div v-for="o in others" :key="o.slug" class="other">
                <div class="other__name">{{ o.name_ru }}</div>
                <div v-if="o.short_story" class="other__story">{{ o.short_story }}</div>
                <div v-if="o.expert_note" class="other__note">{{ o.expert_note }}</div>
              </div>
            </div>
          </section>

          <aside v-if="rec.expert_notes" class="notes">
            <div class="notes__eyebrow">на полях</div>
            <p>{{ rec.expert_notes }}</p>
          </aside>

          <footer class="actions">
            <a :href="pdfUrl" target="_blank" rel="noopener" class="v-btn">
              ✦ скачать pdf ✦
            </a>
            <NuxtLink :to="`/expert/${personId}`" class="v-btn--link">← к экспертному листу</NuxtLink>
          </footer>
        </template>
      </div>
    </div>
  </main>
</template>

<style scoped>
.client-page { max-width: 720px; }
.client-sheet { background: var(--paper); }

.masthead { text-align: center; padding-bottom: 12px; border-bottom: 1px solid var(--rule); }
.symbols {
  color: var(--terra);
  font-size: 16px;
  letter-spacing: 6px;
  margin-bottom: 6px;
}
.title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 36px;
  line-height: 1;
  margin: 0;
  letter-spacing: 0.04em;
}
.sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 4px;
}

.error {
  text-align: center;
  padding: 40px 0;
  font-family: var(--serif);
  font-style: italic;
  color: var(--terra);
}
.error a { color: var(--terra); }

.for { text-align: center; margin: 22px 0 16px; }
.for__label {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.36em;
  text-transform: uppercase;
  color: var(--terra);
}
.for__name {
  font-family: var(--display);
  font-size: 38px;
  line-height: 1;
  margin-top: 6px;
  color: var(--ink);
}

.main-tree {
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  padding: 22px 0 26px;
  text-align: center;
}
.main-tree__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.36em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 18px;
}
.main-tree__name {
  font-family: var(--display);
  font-weight: 400;
  font-size: 38px;
  line-height: 1;
  margin: 16px 0 0;
  color: var(--ink);
}
.main-tree__story {
  font-family: var(--serif);
  font-style: italic;
  font-size: 16px;
  line-height: 1.6;
  margin: 14px auto 0;
  max-width: 440px;
  color: var(--ink);
}

.icon-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 130px;
  height: 130px;
  border: 1px solid var(--ink);
  border-radius: 50%;
  background: var(--paper-deep);
  position: relative;
}
.icon-circle::after {
  content: '';
  position: absolute;
  inset: 10px;
  border: 0.5px solid var(--ink);
  border-radius: 50%;
  opacity: 0.4;
  pointer-events: none;
}
.icon-circle__letter {
  font-family: var(--display);
  font-size: 48px;
  line-height: 1;
  color: var(--ink);
}

.others { margin-top: 26px; }
.others__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.36em;
  text-transform: uppercase;
  color: var(--terra);
  text-align: center;
  margin-bottom: 16px;
}
.others__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.other {
  border: 1px solid var(--rule);
  padding: 12px 14px;
}
.other__name {
  font-family: var(--display);
  font-size: 20px;
  line-height: 1;
  color: var(--ink);
}
.other__story {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  line-height: 1.45;
  color: var(--ink-soft);
  margin-top: 6px;
}
.other__note {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  line-height: 1.45;
  color: var(--ink);
  margin-top: 6px;
  padding: 6px 8px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
}
.main-tree__note {
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  line-height: 1.55;
  color: var(--ink);
  margin: 12px auto 0;
  max-width: 440px;
  padding: 8px 12px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
  text-align: left;
}

.notes {
  margin-top: 24px;
  padding: 14px 16px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
}
.notes__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.36em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 6px;
}
.notes p {
  margin: 0;
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  line-height: 1.6;
  color: var(--ink);
}

.actions {
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid var(--ink);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

@media (max-width: 540px) {
  .others__grid { grid-template-columns: 1fr; }
}
</style>
