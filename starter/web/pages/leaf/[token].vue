<script setup lang="ts">
import type { RecommendationOut, PoolEntry } from '~/composables/useApi'

definePageMeta({
  layout: false,
})

const route = useRoute()
const api = useApi()

const token = computed(() => String(route.params.token))

const { data: rec, error: recError } = await useAsyncData<RecommendationOut>(
  () => `leaf-${token.value}`,
  () => api.getLeaf(token.value),
  { watch: [token] },
)

interface ClientItem {
  slug: string
  name_ru: string
  short_story: string | null
  expert_note: string | null
}

function pick(it: { plant_slug: string; expert_note?: string | null; plant_name_ru?: string | null; plant_short_story?: string | null }): ClientItem {
  // Сперва берём enrichment из curated_pool (приходит с бэка для всех слагов
  // через _enrich_rec_out), потом raw_pool (свежий рекоменд), потом сам slug.
  const raw: PoolEntry | undefined = rec.value?.raw_pool.find((p) => p.plant_slug === it.plant_slug)
  return {
    slug: it.plant_slug,
    name_ru: it.plant_name_ru || raw?.plant_name_ru || it.plant_slug,
    short_story: it.plant_short_story || raw?.plant_short_story || null,
    expert_note: it.expert_note ?? null,
  }
}

const main = computed<ClientItem | null>(() => {
  if (!rec.value || !rec.value.curated_pool?.length) return null
  const items = rec.value.curated_pool
  const titleSlug = rec.value.title_plant_slug || items[0].plant_slug
  const titleItem = items.find((it) => it.plant_slug === titleSlug) ?? items[0]
  return pick(titleItem)
})

const others = computed<ClientItem[]>(() => {
  if (!rec.value || !main.value) return []
  return (rec.value.curated_pool || [])
    .filter((it) => it.plant_slug !== main.value!.slug)
    .map((it) => pick(it))
})

// Имя — из input_snapshot, чтобы публичный лист не подтягивал /persons/{id} (это admin-данные)
const firstName = computed(() => {
  const snap = rec.value?.input_snapshot
  return (snap && typeof snap === 'object' && 'first_name' in snap)
    ? String(snap.first_name || 'госпожа')
    : 'госпожа'
})

function fmtCreated(s: string | undefined): string {
  if (!s) return ''
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })
}
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

        <div v-if="recError" class="error">
          лист не&nbsp;найден или ссылка устарела.
        </div>

        <template v-else-if="rec">
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
            <div class="notes__eyebrow">тема сада</div>
            <p>{{ rec.expert_notes }}</p>
          </aside>

          <div class="signature">
            <span class="signature__line"></span>
            <span class="signature__text">
              составлено <em>{{ fmtCreated(rec.created_at) }}</em>
            </span>
          </div>
        </template>
      </div>
    </div>
  </main>
</template>

<style scoped>
.client-page { max-width: 720px; }
.client-sheet { background: var(--paper); }

.masthead { text-align: center; padding-bottom: 12px; border-bottom: 1px solid var(--rule); }
.symbols { color: var(--terra); font-size: 16px; letter-spacing: 6px; margin-bottom: 6px; }
.title { font-family: var(--display); font-weight: 400; font-size: 36px; line-height: 1; margin: 0; letter-spacing: 0.04em; }
.sub { font-family: var(--serif); font-style: italic; font-size: 13px; color: var(--ink-faded); margin-top: 4px; }

.error {
  text-align: center;
  padding: 40px 0;
  font-family: var(--serif);
  font-style: italic;
  color: var(--terra);
}

.for { text-align: center; margin: 22px 0 16px; }
.for__label {
  font-family: var(--sans); font-weight: 500; font-size: 9px;
  letter-spacing: 0.36em; text-transform: uppercase; color: var(--terra);
}
.for__name {
  font-family: var(--display); font-size: 38px; line-height: 1;
  margin-top: 6px; color: var(--ink);
}

.main-tree {
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  padding: 22px 0 26px;
  text-align: center;
}
.main-tree__eyebrow {
  font-family: var(--sans); font-weight: 500; font-size: 9px;
  letter-spacing: 0.36em; text-transform: uppercase; color: var(--terra);
  margin-bottom: 18px;
}
.main-tree__name {
  font-family: var(--display); font-weight: 400; font-size: 38px;
  line-height: 1; margin: 16px 0 0; color: var(--ink);
}
.main-tree__story {
  font-family: var(--serif); font-style: italic; font-size: 16px;
  line-height: 1.6; margin: 14px auto 0; max-width: 440px; color: var(--ink);
}
.main-tree__note {
  font-family: var(--serif); font-style: italic; font-size: 15px;
  line-height: 1.55; color: var(--ink);
  margin: 12px auto 0; max-width: 440px;
  padding: 8px 12px; background: var(--paper-deep);
  border-left: 2px solid var(--terra); text-align: left;
}

.icon-circle {
  display: inline-flex; align-items: center; justify-content: center;
  width: 130px; height: 130px;
  border: 1px solid var(--ink); border-radius: 50%;
  background: var(--paper-deep); position: relative;
}
.icon-circle::after {
  content: ''; position: absolute; inset: 10px;
  border: 0.5px solid var(--ink); border-radius: 50%;
  opacity: 0.4; pointer-events: none;
}
.icon-circle__letter {
  font-family: var(--display); font-size: 48px; line-height: 1; color: var(--ink);
}

.others { margin-top: 26px; }
.others__eyebrow {
  font-family: var(--sans); font-weight: 500; font-size: 9px;
  letter-spacing: 0.36em; text-transform: uppercase; color: var(--terra);
  text-align: center; margin-bottom: 16px;
}
.others__grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.other { border: 1px solid var(--rule); padding: 12px 14px; }
.other__name {
  font-family: var(--display); font-size: 20px; line-height: 1; color: var(--ink);
}
.other__story {
  font-family: var(--serif); font-style: italic; font-size: 14px;
  line-height: 1.45; color: var(--ink-soft); margin-top: 6px;
}
.other__note {
  font-family: var(--serif); font-style: italic; font-size: 14px;
  line-height: 1.45; color: var(--ink); margin-top: 6px;
  padding: 6px 8px; background: var(--paper-deep);
  border-left: 2px solid var(--terra);
}

.notes {
  margin-top: 24px;
  padding: 14px 16px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
}
.notes__eyebrow {
  font-family: var(--sans); font-weight: 500; font-size: 8px;
  letter-spacing: 0.36em; text-transform: uppercase; color: var(--terra);
  margin-bottom: 6px;
}
.notes p {
  margin: 0; font-family: var(--serif); font-style: italic;
  font-size: 15px; line-height: 1.6; color: var(--ink);
}

.signature {
  margin-top: 28px;
  text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding-bottom: 18px;
}
.signature__line { display: block; width: 120px; border-bottom: 1px solid var(--ink); }
.signature__text {
  font-family: var(--serif); font-style: italic; font-size: 14px; color: var(--ink-faded);
}
.signature__text em { color: var(--ink); font-style: italic; }

@media (max-width: 540px) { .others__grid { grid-template-columns: 1fr; } }
</style>
