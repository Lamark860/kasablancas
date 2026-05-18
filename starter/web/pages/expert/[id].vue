<script setup lang="ts">
import type { OracleInfo, Person, RecommendOutput, RecommendationOut, RecommendationSummary } from '~/composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()

const personId = computed(() => Number(route.params.id))

// — Два независимых фильтра, согласно макету Prototype-v2
const frost = ref(true)         // выживет в саду: USDA + sun + soil + tree-enemy
const hideWeeds = ref(true)     // приглушить агрессивные/сорные

const disabledOracles = ref<Set<string>>(new Set())
const disabledKey = computed(() => Array.from(disabledOracles.value).sort().join(','))
const filtersKey = computed(() => `${frost.value}-${hideWeeds.value}`)

const { data: person, error: personError } = await useAsyncData<Person>(
  () => `person-${personId.value}`,
  () => api.getPerson(personId.value),
  { watch: [personId] },
)

const { data: result, pending, refresh, error: recError } = await useAsyncData<RecommendOutput>(
  () => `rec-${personId.value}-${filtersKey.value}-${disabledKey.value}`,
  () => api.recommend(personId.value, {
    frost: frost.value,
    hideWeeds: hideWeeds.value,
    disabledOracles: Array.from(disabledOracles.value),
  }),
  { watch: [personId, filtersKey, disabledKey] },
)

const { data: allOracles } = await useAsyncData<OracleInfo[]>(
  'oracles',
  () => api.listOracles(),
)

const recomputeFlash = ref(false)
let flashTimer: ReturnType<typeof setTimeout> | null = null
watch(disabledKey, () => {
  recomputeFlash.value = true
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => (recomputeFlash.value = false), 1400)
})

function toggleOracleDisabled(oracleId: string) {
  const next = new Set(disabledOracles.value)
  if (next.has(oracleId)) next.delete(oracleId)
  else next.add(oracleId)
  disabledOracles.value = next
}

const saved = ref<RecommendationOut | null>(null)
async function loadSaved() {
  try { saved.value = await api.getCurated(personId.value) }
  catch { saved.value = null }
}
await loadSaved()

const history = ref<RecommendationSummary[]>([])
async function loadHistory() {
  try { history.value = await api.listRecommendations(personId.value) }
  catch { history.value = [] }
}
await loadHistory()

function formatDate(s: string): string {
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  return d.toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

async function loadVersion(rec: RecommendationSummary) {
  try {
    const full = await api.getRecommendationVersion(personId.value, rec.id)
    curated.value = _initCurated(full.curated_pool)
    titleSlug.value = full.title_plant_slug
    expertNotes.value = full.expert_notes ?? ''
  } catch (e: any) {
    saveError.value = `не удалось загрузить версию #${rec.id}: ${e?.message || 'ошибка'}`
  }
}

async function finalizeVersion(rec: RecommendationSummary) {
  if (!window.confirm(
    `Пометить версию от ${formatDate(rec.created_at)} как финальную? Флаг снимется с предыдущих.`
  )) return
  try {
    await api.finalizeRecommendation(personId.value, rec.id)
    await loadHistory()
  } catch (e: any) {
    saveError.value = `не удалось финализировать #${rec.id}: ${e?.message || 'ошибка'}`
  }
}

function _initCurated(items: any): Map<string, string> {
  const m = new Map<string, string>()
  for (const it of items ?? []) m.set(it.plant_slug, it.expert_note || '')
  return m
}

const curated = ref<Map<string, string>>(_initCurated(saved.value?.curated_pool))
const titleSlug = ref<string | null>(saved.value?.title_plant_slug ?? null)
const expertNotes = ref<string>(saved.value?.expert_notes ?? '')

watch(saved, (s) => {
  curated.value = _initCurated(s?.curated_pool)
  titleSlug.value = s?.title_plant_slug ?? null
  expertNotes.value = s?.expert_notes ?? ''
})

function toggleCurated(slug: string) {
  const next = new Map(curated.value)
  if (next.has(slug)) {
    next.delete(slug)
    if (titleSlug.value === slug) titleSlug.value = null
  } else {
    next.set(slug, '')
    if (!titleSlug.value) titleSlug.value = slug
  }
  curated.value = next
}
function setTitle(slug: string) { titleSlug.value = slug }
function updateNote(slug: string, note: string) {
  if (!curated.value.has(slug)) return
  const next = new Map(curated.value)
  next.set(slug, note)
  curated.value = next
}

const saving = ref(false)
const saveError = ref<string | null>(null)

async function saveRecommendation(mode: 'version' | 'open-leaf') {
  if (!curated.value.size) {
    saveError.value = 'отметьте хотя бы одно растение в коллекции'
    return
  }
  saveError.value = null
  saving.value = true
  try {
    const items = Array.from(curated.value, ([plant_slug, note]) => ({
      plant_slug,
      expert_note: note?.trim() ? note.trim() : null,
    }))
    await api.saveCurated(personId.value, {
      curated: items,
      title_plant_slug: titleSlug.value,
      expert_notes: expertNotes.value || null,
      apply_filters: frost.value || hideWeeds.value,
    })
    await loadHistory()
    if (mode === 'open-leaf') {
      await router.push(`/client/${personId.value}`)
    } else {
      // «сохранить как версию» — остаёмся, подгружаем заново
      await loadSaved()
    }
  } catch (e: any) {
    saveError.value = e?.data?.detail
      ? JSON.stringify(e.data.detail)
      : (e?.message || 'неизвестная ошибка')
  } finally {
    saving.value = false
  }
}

const fullName = computed(() => {
  if (!person.value) return ''
  const p = person.value
  return [p.last_name, p.first_name, p.middle_name].filter(Boolean).join(' ') || p.first_name
})
const firstName = computed(() => person.value?.first_name || '—')
const guestInitial = computed(() => (firstName.value || '?')[0].toUpperCase())
const curatedCount = computed(() => curated.value.size)

const electaList = computed(() => {
  if (!result.value) return []
  return result.value.pool.filter(p => curated.value.has(p.plant_slug))
})
const silvaList = computed(() => {
  if (!result.value) return []
  return result.value.pool.filter(p => !curated.value.has(p.plant_slug))
})

// Запоминаем slug → reason при включённом frost для подсветки «новых»
const lastExcludedBySlug = ref<Map<string, string>>(new Map())
watch(result, (r) => {
  if (r && r.frost) {
    const m = new Map<string, string>()
    for (const ex of r.excluded || []) m.set(ex.plant_slug, ex.reason)
    lastExcludedBySlug.value = m
  }
}, { immediate: true })

const lastExcludedCount = computed(() => lastExcludedBySlug.value.size)

function frostReasonFor(slug: string): string | null {
  const r = lastExcludedBySlug.value.get(slug)
  if (!r) return null
  return /USDA/i.test(r) ? r : null
}

function isNew(slug: string): boolean {
  return !!result.value && !result.value.frost && lastExcludedBySlug.value.has(slug)
}

interface VersionDiff {
  added: string[]
  removed: string[]
  titleChanged: { from: string | null; to: string | null } | null
  unchanged: boolean
}

function diffAgainstCurrent(rec: RecommendationSummary): VersionDiff {
  const histSlugs = new Set((rec.curated_pool || []).map(it => it.plant_slug))
  const curSlugs = new Set(curated.value.keys())
  const added = [...histSlugs].filter(s => !curSlugs.has(s))
  const removed = [...curSlugs].filter(s => !histSlugs.has(s))
  const titleDiff = rec.title_plant_slug !== titleSlug.value
    ? { from: titleSlug.value, to: rec.title_plant_slug }
    : null
  return {
    added,
    removed,
    titleChanged: titleDiff,
    unchanged: added.length === 0 && removed.length === 0 && titleDiff === null,
  }
}

// Локальный латинский подзаголовок для fontes (макет требует name + lat-курсив)
const oracleLatin: Record<string, string> = {
  druid_tree: 'arbores druidum',
  druid_flower: 'flores druidum',
  zodiac: 'zodiacus',
  slavic: 'annus slavicus',
  numerology: 'numerus nominis',
  eye_color: 'color oculorum',
  name: 'planta nominis',
  lunar: 'dies lunæ',
}
</script>

<template>
  <main class="v-page v-page--wide expert-page">
    <div class="v-sheet v-grain">
      <div class="v-frame">
        <header class="masthead">
          <div class="masthead__brand">
            <span class="brand__sigil">☉ ☾ ✦</span>
            <h1 class="brand__title">Hortus <span class="brand__amp">&amp;</span> Animæ</h1>
          </div>
          <div class="masthead__caps">
            <span>folium ii · expertus tantum</span>
            <span class="masthead__sub">свод растений · не для гостьи</span>
          </div>
        </header>

        <!-- Гостья-баннер -->
        <div v-if="person" class="guest-bar">
          <div class="guest-bar__mono" aria-hidden="true">{{ guestInitial }}</div>
          <div class="guest-bar__main">
            <div class="guest-bar__name">{{ fullName }}</div>
            <div class="guest-bar__meta">
              <span v-if="person.birth_date">{{ person.birth_date }}</span>
              <span v-if="person.birth_place"> · {{ person.birth_place }}</span>
            </div>
          </div>
          <div class="guest-bar__tags">
            <span v-if="person.garden_zone_usda" class="guest-bar__tag">
              климзона <strong>{{ person.garden_zone_usda }}</strong>
            </span>
            <span v-if="person.eye_color" class="guest-bar__tag">
              взгляд <em>{{ person.eye_color }}</em>
            </span>
          </div>
        </div>

        <div v-if="personError" class="error">гостья #{{ personId }} не найдена</div>
        <div v-else-if="recError" class="error">оракулы не свелись: {{ recError.message }}</div>

        <div v-else class="layout3">
          <!-- LEFT: fontes + filtra -->
          <aside class="col col--left">
            <section class="v-aside fontes">
              <h3 class="aside__heading">fontes — источники</h3>
              <ul class="oracle-list">
                <li
                  v-for="o in allOracles || []"
                  :key="o.id"
                  class="oracle-list__row"
                  :class="{ 'oracle-list__row--disabled': disabledOracles.has(o.id) || !o.active || !o.implemented }"
                >
                  <label class="oracle-list__label">
                    <input
                      type="checkbox"
                      :checked="!disabledOracles.has(o.id) && !!o.active && o.implemented"
                      :disabled="!o.implemented || !o.active"
                      @change="toggleOracleDisabled(o.id)"
                    />
                    <span class="oracle-list__name">
                      {{ o.name_ru }}
                      <em class="oracle-list__lat">{{ oracleLatin[o.id] || o.id }}</em>
                    </span>
                  </label>
                  <span v-if="!o.implemented" class="oracle-list__status" title="оракул в роадмапе">⏸</span>
                  <span v-else-if="!o.active" class="oracle-list__status" title="отключён в БД">×</span>
                </li>
              </ul>
              <transition name="fontes-flash">
                <div v-if="recomputeFlash" class="fontes__flash">свод пересчитан…</div>
              </transition>
            </section>

            <section class="v-aside filtra">
              <h3 class="aside__heading">filtra — ограничения</h3>
              <label class="filtra__row">
                <input type="checkbox" v-model="frost" />
                <span class="filtra__main">
                  пройдёт зимовку
                  <span v-if="person?.garden_zone_usda" class="filtra__hint">(зона ≥ {{ person.garden_zone_usda }})</span>
                </span>
                <span class="filtra__caption">USDA + почва + свет + дерево-враг</span>
              </label>
              <label class="filtra__row">
                <input type="checkbox" v-model="hideWeeds" />
                <span class="filtra__main">приглушить сорные</span>
                <span class="filtra__caption">is_weed_like × 0.5</span>
              </label>
            </section>
          </aside>

          <!-- MAIN -->
          <section class="col col--main">
            <header class="main__head">
              <div>
                <div class="main__eyebrow">tabula plantarum</div>
                <h2 class="main__title">Свод <em>растений</em></h2>
              </div>
              <div class="main__hint">
                отметьте 3–5 в&nbsp;коллекцию, одну — главным деревом
              </div>
            </header>

            <div v-if="pending" class="loading">сводим…</div>

            <div v-else-if="result && result.pool.length === 0" class="empty">
              ни один оракул не дал голоса. проверьте дату рождения или фильтры.
            </div>

            <template v-else-if="result">
              <div
                class="filter-state"
                :class="{ 'filter-state--off': !result.frost }"
                v-if="result.frost || lastExcludedCount > 0"
              >
                <span class="filter-state__text">
                  <template v-if="result.frost">
                    пул отфильтрован по&nbsp;климзоне.
                    <strong>{{ result.excluded?.length ?? 0 }}</strong>
                    {{ (result.excluded?.length ?? 0) === 1 ? 'растение' : 'растений' }}
                    отложено в&nbsp;<em>exclusi</em>
                  </template>
                  <template v-else>
                    показан сырой пул. <strong>+{{ lastExcludedCount }}</strong>
                    за пределами зоны
                  </template>
                </span>
                <button
                  type="button"
                  class="filter-state__toggle"
                  @click="frost = !frost"
                >
                  {{ result.frost ? 'показать сырой пул' : '↺ вернуть фильтр' }}
                </button>
              </div>

              <section class="section section--electa">
                <header class="section__head">
                  <h3 class="section__title">electa</h3>
                  <span class="section__sub">
                    избранные · <strong>{{ electaList.length }}</strong> из 3–5
                    <span v-if="titleSlug" class="section__sub-mark"> · ✦ главное дерево отмечено</span>
                  </span>
                </header>
                <div v-if="electaList.length === 0" class="section__empty">
                  ещё ни&nbsp;одного. кликни <em>«+ в коллекцию»</em> на&nbsp;карточке ниже.
                </div>
                <PlantCard
                  v-for="(entry, i) in electaList"
                  :key="entry.plant_slug"
                  :entry="entry"
                  :index="i"
                  curatable
                  :curated="true"
                  :is-title="titleSlug === entry.plant_slug"
                  :curated-note="curated.get(entry.plant_slug) ?? null"
                  :is-new="isNew(entry.plant_slug)"
                  :frost-reason="frostReasonFor(entry.plant_slug)"
                  @toggle-curated="toggleCurated"
                  @set-title="setTitle"
                  @update-note="updateNote"
                />
              </section>

              <section v-if="silvaList.length" class="section section--silva">
                <header class="section__head">
                  <h3 class="section__title">silva</h3>
                  <span class="section__sub">резерв · <strong>{{ silvaList.length }}</strong></span>
                </header>
                <PlantCard
                  v-for="(entry, i) in silvaList"
                  :key="entry.plant_slug"
                  :entry="entry"
                  :index="electaList.length + i"
                  curatable
                  :curated="false"
                  :is-title="false"
                  :curated-note="null"
                  :is-new="isNew(entry.plant_slug)"
                  :frost-reason="frostReasonFor(entry.plant_slug)"
                  @toggle-curated="toggleCurated"
                  @set-title="setTitle"
                  @update-note="updateNote"
                />
              </section>

              <footer class="main__footer">
                <NuxtLink to="/registry" class="v-btn--link">← к реестру</NuxtLink>
                <button
                  type="button"
                  class="v-btn--link main__footer-version"
                  :disabled="saving || !curatedCount"
                  @click="saveRecommendation('version')"
                >сохранить как версию</button>
                <button
                  type="button"
                  class="v-btn save-btn"
                  :disabled="saving || !curatedCount"
                  @click="saveRecommendation('open-leaf')"
                >{{ saving ? 'сохраняем…' : 'сохранить и открыть лист гостьи →' }}</button>
              </footer>
              <div v-if="saveError" class="save-error">{{ saveError }}</div>
            </template>
          </section>

          <!-- RIGHT: collectio + exclusi + historiae -->
          <aside class="col col--right" v-if="result">
            <section class="v-aside curated-summary">
              <h3 class="aside__heading">collectio</h3>
              <div class="curated-summary__count">
                <strong>{{ curatedCount }}</strong> в&nbsp;коллекции
                <span v-if="titleSlug" class="curated-summary__title">· главное: <em>{{ titleSlug }}</em></span>
              </div>
              <label class="notes">
                <span class="notes__label">общая заметка (тема сада)</span>
                <textarea
                  v-model="expertNotes"
                  class="notes__area"
                  rows="3"
                  placeholder="комментарий к листу гостьи…"
                />
              </label>
            </section>

            <section v-if="result.excluded.length" class="v-aside excluded">
              <h3 class="aside__heading">exclusi — отложены</h3>
              <div v-for="ex in result.excluded" :key="ex.plant_slug" class="excluded__row">
                <div class="excluded__name">{{ ex.plant_slug }}</div>
                <div class="excluded__reason">{{ ex.reason }}</div>
                <button
                  type="button"
                  class="excluded__restore"
                  title="снять frost-фильтр — пул вернётся к сырому виду"
                  @click="frost = false"
                >↺ вернуть</button>
              </div>
            </section>

            <section v-if="history.length > 1" class="v-aside history">
              <h3 class="aside__heading">historiae — версии</h3>
              <ul class="history__list">
                <li
                  v-for="(h, i) in history"
                  :key="h.id"
                  class="history__row"
                  :class="{ 'history__row--current': i === 0 }"
                >
                  <div class="history__meta">
                    <span class="history__date">{{ formatDate(h.created_at) }}</span>
                    <span v-if="i === 0" class="history__badge">текущая</span>
                    <span v-if="h.is_final" class="history__badge history__badge--final" title="отдана гостье">finalis</span>
                  </div>
                  <div class="history__summary">
                    <span v-if="h.title_plant_slug">главное: <em>{{ h.title_plant_name_ru || h.title_plant_slug }}</em> · </span>
                    <span>{{ h.curated_pool?.length ?? 0 }} в&nbsp;избр.</span>
                  </div>
                  <div v-if="i !== 0" class="history__diff">
                    <template v-if="diffAgainstCurrent(h).unchanged">
                      <span class="history__diff-empty">≡ совпадает с текущей</span>
                    </template>
                    <template v-else>
                      <span v-for="slug in diffAgainstCurrent(h).added" :key="`a-${slug}`" class="history__diff-add">+ {{ slug }}</span>
                      <span v-for="slug in diffAgainstCurrent(h).removed" :key="`r-${slug}`" class="history__diff-rm">− {{ slug }}</span>
                      <span v-if="diffAgainstCurrent(h).titleChanged" class="history__diff-title">
                        → <em>{{ diffAgainstCurrent(h).titleChanged.to || '—' }}</em>
                      </span>
                    </template>
                  </div>
                  <div class="history__buttons">
                    <button type="button" class="v-btn--link history__load" @click="loadVersion(h)">↘ форкнуть</button>
                    <button v-if="!h.is_final" type="button" class="v-btn--link history__finalize" @click="finalizeVersion(h)">✦ финальная</button>
                  </div>
                </li>
              </ul>
            </section>
          </aside>
        </div>

        <footer class="page-foot">
          <span>folium ii · expertus · internal use</span>
          <button class="v-btn--link" type="button" @click="refresh()">↻ пересобрать</button>
        </footer>
      </div>
    </div>
  </main>
</template>

<style scoped>
.expert-page { max-width: 1480px; }

.masthead {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px double var(--rule);
  padding-bottom: 14px;
  margin-bottom: 16px;
}
.brand__sigil {
  color: var(--terra);
  font-size: 14px;
  letter-spacing: 6px;
  display: block;
  margin-bottom: 2px;
}
.brand__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 38px;
  line-height: 1;
  margin: 0;
  letter-spacing: 0.02em;
  color: var(--ink);
}
.brand__amp { color: var(--terra); font-style: italic; }
.masthead__caps {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--ink-faded);
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.masthead__sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 12px;
  letter-spacing: 0;
  text-transform: none;
  color: var(--ink-faded);
}

/* — Guest banner — */
.guest-bar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 18px;
  align-items: center;
  padding: 12px 16px;
  background: var(--paper-warm, #ebe0c2);
  border: 1px solid var(--rule);
  margin-bottom: 20px;
}
.guest-bar__mono {
  width: 50px; height: 50px;
  display: flex; align-items: center; justify-content: center;
  border: 1.5px solid var(--ink);
  border-radius: 50%;
  font-family: var(--display);
  font-size: 24px;
  color: var(--ink);
}
.guest-bar__name {
  font-family: var(--display);
  font-size: 22px;
  line-height: 1;
  color: var(--ink);
}
.guest-bar__meta {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 4px;
}
.guest-bar__tags { display: flex; gap: 12px; }
.guest-bar__tag {
  font-family: var(--serif);
  font-size: 13px;
  font-style: italic;
  color: var(--ink-faded);
}
.guest-bar__tag strong, .guest-bar__tag em {
  color: var(--ink);
  font-style: normal;
}

/* — 3-колонная — */
.layout3 {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 24px;
  align-items: flex-start;
}
.col--left, .col--right {
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: sticky;
  top: 16px;
}

/* — Headings sidebar — */
.aside__heading {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--terra);
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--rule);
}

/* — Fontes — */
.oracle-list { list-style: none; margin: 0; padding: 0; }
.oracle-list__row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 6px 0;
  border-bottom: 1px dotted var(--rule);
}
.oracle-list__row:last-child { border-bottom: none; }
.oracle-list__row--disabled .oracle-list__name {
  color: var(--ink-faded);
  text-decoration: line-through;
  text-decoration-color: var(--rule);
}
.oracle-list__label {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  cursor: pointer;
  flex: 1;
}
.oracle-list__label input { margin-top: 3px; cursor: inherit; }
.oracle-list__label input:disabled { cursor: not-allowed; }
.oracle-list__name {
  font-family: var(--serif);
  font-size: 14px;
  line-height: 1.25;
  color: var(--ink);
  display: flex;
  flex-direction: column;
}
.oracle-list__lat {
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-faded);
  margin-top: 1px;
}
.oracle-list__status {
  font-family: var(--sans);
  font-size: 11px;
  color: var(--ink-faded);
  cursor: help;
}

.fontes { position: relative; }
.fontes__flash {
  margin-top: 10px;
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--terra);
}
.fontes-flash-enter-active, .fontes-flash-leave-active { transition: opacity 0.4s ease; }
.fontes-flash-enter-from, .fontes-flash-leave-to { opacity: 0; }

/* — Filtra — */
.filtra__row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 10px;
  align-items: baseline;
  padding: 6px 0;
  cursor: pointer;
  border-bottom: 1px dotted var(--rule);
}
.filtra__row:last-child { border-bottom: none; }
.filtra__row input { margin-top: 3px; cursor: inherit; }
.filtra__main {
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
}
.filtra__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 12px;
  color: var(--terra);
}
.filtra__caption {
  grid-column: 2;
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-faded);
}

/* — Main — */
.main__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 16px;
}
.main__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--terra);
}
.main__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 30px;
  line-height: 1;
  margin: 4px 0 0;
  color: var(--ink);
}
.main__title em { color: var(--terra); font-style: italic; }
.main__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  text-align: right;
  max-width: 240px;
}

.loading, .empty, .error {
  font-family: var(--serif);
  font-style: italic;
  font-size: 16px;
  color: var(--ink-faded);
  padding: 24px 0;
}
.error { color: var(--terra); }

/* — Filter-state — */
.filter-state {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  margin-bottom: 14px;
  border-left: 4px solid var(--terra);
  background: rgba(139, 58, 31, 0.06);
}
.filter-state--off {
  border-left-color: var(--gold, #b08d44);
  background: rgba(176, 141, 68, 0.12);
}
.filter-state__text {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink);
}
.filter-state__text strong { color: var(--terra); font-style: normal; }
.filter-state__text em { color: var(--terra); font-style: italic; }
.filter-state--off .filter-state__text strong { color: #7a5e22; }
.filter-state__toggle {
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
.filter-state__toggle:hover { border-color: var(--ink); }

/* — Section headers — */
.section { margin-top: 20px; }
.section__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--rule);
}
.section--electa .section__head { border-bottom-color: var(--terra); }
.section__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 22px;
  line-height: 1;
  margin: 0;
  color: var(--ink);
}
.section__sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}
.section__sub strong { color: var(--ink); font-style: normal; }
.section__sub-mark { color: var(--terra); }
.section__empty {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  padding: 14px 14px;
  background: var(--paper-deep);
  border-left: 2px dotted var(--rule);
  margin-top: 10px;
}
.section__empty em { color: var(--terra); }

/* — Main footer (2 кнопки save) — */
.main__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--ink);
  gap: 14px;
}
.main__footer-version {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faded);
  background: transparent;
  border: 1px dashed var(--rule);
  padding: 8px 12px;
  cursor: pointer;
  white-space: nowrap;
}
.main__footer-version:hover:not(:disabled) { color: var(--ink); border-color: var(--ink); }
.main__footer-version:disabled { opacity: 0.4; cursor: not-allowed; }
.save-btn { padding: 12px 18px; }
.save-error {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
  margin-top: 8px;
  text-align: right;
}

/* — Collectio (right top) — */
.curated-summary__count {
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
}
.curated-summary__count strong {
  font-family: var(--display);
  font-size: 18px;
}
.curated-summary__title em { color: var(--terra); font-style: italic; }
.notes { display: block; margin-top: 12px; }
.notes__label {
  display: block;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 4px;
}
.notes__area {
  width: 100%;
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink);
  background: var(--paper-deep);
  border: 1px solid var(--rule);
  padding: 8px 10px;
  resize: vertical;
  outline: none;
}
.notes__area:focus { border-color: var(--terra); }

/* — Exclusi — */
.excluded__row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 6px 10px;
  padding: 6px 0;
  border-bottom: 1px dotted var(--rule);
}
.excluded__row:last-child { border-bottom: none; }
.excluded__name {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink);
  text-decoration: line-through;
  text-decoration-color: var(--terra);
}
.excluded__reason {
  grid-column: 1;
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-faded);
  margin-top: -2px;
}
.excluded__restore {
  grid-column: 2;
  grid-row: 1 / 3;
  align-self: center;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  background: transparent;
  border: 1px solid var(--rule);
  padding: 4px 8px;
  cursor: pointer;
  white-space: nowrap;
}
.excluded__restore:hover { background: var(--terra); color: var(--paper); border-color: var(--terra); }

/* — Historiae — */
.history__list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.history__row {
  border-bottom: 1px dotted var(--rule);
  padding-bottom: 8px;
  display: flex; flex-direction: column; gap: 3px;
}
.history__row:last-child { border-bottom: none; }
.history__row--current { background: var(--paper-deep); padding: 6px 8px; border-radius: 1px; }
.history__meta {
  display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;
}
.history__date {
  font-family: var(--serif); font-size: 13px; color: var(--ink);
}
.history__badge {
  font-family: var(--sans); font-weight: 500;
  font-size: 8px; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--terra);
}
.history__badge--final {
  padding: 1px 6px;
  background: var(--terra); color: var(--paper);
}
.history__summary {
  font-family: var(--serif); font-style: italic;
  font-size: 12px; color: var(--ink-faded);
}
.history__summary em { color: var(--terra); }
.history__diff {
  display: flex; flex-wrap: wrap; gap: 4px 6px; margin-top: 4px;
  font-family: var(--sans); font-size: 10px;
}
.history__diff-add { color: #2da44e; }
.history__diff-rm { color: #d4380d; text-decoration: line-through; }
.history__diff-title {
  color: var(--terra); font-family: var(--serif); font-style: italic; font-size: 11px;
}
.history__diff-title em { font-style: italic; color: var(--ink); }
.history__diff-empty {
  color: var(--ink-faded); font-family: var(--serif); font-style: italic; font-size: 11px;
}
.history__buttons { display: flex; gap: 10px; justify-content: flex-end; margin-top: 4px; }
.history__load, .history__finalize {
  font-family: var(--sans); font-weight: 500;
  font-size: 8px; letter-spacing: 0.18em; text-transform: uppercase;
  background: none; border: none; cursor: pointer;
}
.history__load { color: var(--terra); }
.history__load:hover { color: var(--ink); }
.history__finalize { color: var(--gold, #b08d44); }
.history__finalize:hover { color: var(--terra); }

/* — Page foot — */
.page-foot {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 32px; padding-top: 14px;
  border-top: 1px solid var(--ink);
  font-family: var(--serif); font-style: italic; font-size: 13px; color: var(--ink-faded);
}

@media (max-width: 1280px) {
  .layout3 { grid-template-columns: 1fr 320px; }
  .col--left { display: none; }
}
@media (max-width: 900px) {
  .layout3 { grid-template-columns: 1fr; }
  .col--right { position: static; }
}
</style>
