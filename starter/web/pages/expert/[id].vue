<script setup lang="ts">
import type { OracleInfo, Person, RecommendOutput, RecommendationOut, RecommendationSummary } from '~/composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()

const personId = computed(() => Number(route.params.id))
const applyFilters = ref(true)
const disabledOracles = ref<Set<string>>(new Set())
const disabledKey = computed(() => Array.from(disabledOracles.value).sort().join(','))

const { data: person, error: personError } = await useAsyncData<Person>(
  () => `person-${personId.value}`,
  () => api.getPerson(personId.value),
  { watch: [personId] },
)

const { data: result, pending, refresh, error: recError } = await useAsyncData<RecommendOutput>(
  () => `rec-${personId.value}-${applyFilters.value}-${disabledKey.value}`,
  () => api.recommend(personId.value, applyFilters.value, Array.from(disabledOracles.value)),
  { watch: [personId, applyFilters, disabledKey] },
)

// Полный список оракулов из БД (включая выключенные active=0) — нужен для
// рендера fontes-сайдбара с чекбоксами всех источников.
const { data: allOracles } = await useAsyncData<OracleInfo[]>(
  'oracles',
  () => api.listOracles(),
)

// Курсивная вспышка «свод пересчитан…» при изменении набора оракулов
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

// Подтягиваем сохранённую кураторскую сборку (если есть). 404 — нормально.
const saved = ref<RecommendationOut | null>(null)
async function loadSaved() {
  try { saved.value = await api.getCurated(personId.value) }
  catch { saved.value = null }
}
await loadSaved()

// История версий (D8). Загружаем мягко — 404 не ломает страницу.
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
    // подменяем local state — но НЕ сохраняем сразу. Эксперт жмёт «сохранить»
    // если хочет создать новую версию из этой.
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

// curated: Map<plant_slug, expert_note>. Наличие ключа означает «в избранном».
function _initCurated(items: typeof saved.value extends infer T ? T extends { curated_pool: infer P } ? P : never : never): Map<string, string> {
  const m = new Map<string, string>()
  for (const it of items ?? []) m.set(it.plant_slug, it.expert_note || '')
  return m
}

const curated = ref<Map<string, string>>(_initCurated(saved.value?.curated_pool))
const titleSlug = ref<string | null>(saved.value?.title_plant_slug ?? null)
const expertNotes = ref<string>(saved.value?.expert_notes ?? '')

// Если saved загрузилась после хидрации — синхронизируем local state.
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
function setTitle(slug: string) {
  titleSlug.value = slug
}
function updateNote(slug: string, note: string) {
  if (!curated.value.has(slug)) return
  const next = new Map(curated.value)
  next.set(slug, note)
  curated.value = next
}

const saving = ref(false)
const saveError = ref<string | null>(null)

async function saveAndOpenClient() {
  if (!curated.value.size) {
    saveError.value = 'отметьте хотя бы одно растение в избранное'
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
      apply_filters: applyFilters.value,
    })
    await loadHistory()
    await router.push(`/client/${personId.value}`)
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
const curatedCount = computed(() => curated.value.size)

const electaList = computed(() => {
  if (!result.value) return []
  return result.value.pool.filter(p => curated.value.has(p.plant_slug))
})
const silvaList = computed(() => {
  if (!result.value) return []
  return result.value.pool.filter(p => !curated.value.has(p.plant_slug))
})

// При включённом фильтре запоминаем slug → reason для исключённых, чтобы
// при выключении подсветить добавленные карточки золотой рамкой + ❋ tooltip.
const lastExcludedBySlug = ref<Map<string, string>>(new Map())
watch(result, (r) => {
  if (r && r.filters_applied) {
    const m = new Map<string, string>()
    for (const ex of r.excluded || []) m.set(ex.plant_slug, ex.reason)
    lastExcludedBySlug.value = m
  }
}, { immediate: true })

const lastExcludedCount = computed(() => lastExcludedBySlug.value.size)

function frostReasonFor(slug: string): string | null {
  // только USDA-причина даёт маркер ❋ «не зимует». Дерево-врага и weed-понижение
  // не про мороз и в маркер не идут.
  const r = lastExcludedBySlug.value.get(slug)
  if (!r) return null
  return /USDA/i.test(r) ? r : null
}

function isNew(slug: string): boolean {
  // «новая» = была бы скрыта фильтром, но фильтр сейчас снят
  return !!result.value && !result.value.filters_applied && lastExcludedBySlug.value.has(slug)
}

// — Diff между текущей версией и каждой исторической (E1).
//   Считаем относительно текущего local state (curated + titleSlug),
//   а не относительно «последней сохранённой» — так эксперт видит,
//   что добавить/убрать в собираемой версии, если форкнет старую.
interface VersionDiff {
  added: string[]      // есть в исторической, нет в текущей
  removed: string[]    // есть в текущей, нет в исторической
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
</script>

<template>
  <main class="v-page v-page--wide">
    <div class="v-sheet v-grain">
      <div class="v-frame">
        <header class="masthead">
          <div class="masthead__left">
            <div class="masthead__symbols" aria-hidden="true">☉ ☾ ✦</div>
            <h1 class="masthead__title">Hortus Animæ</h1>
            <div class="masthead__sub">folium II · expertus tantum · не для гостьи</div>
          </div>
          <div class="masthead__right" v-if="person">
            <div class="masthead__for">составлено для</div>
            <div class="masthead__name">{{ firstName }}</div>
            <div class="masthead__meta">
              {{ person.birth_date }}
              <template v-if="person.birth_place"> · {{ person.birth_place }}</template>
              <template v-if="person.eye_color"> · взгляд {{ person.eye_color }}</template>
              <template v-if="person.garden_zone_usda"> · зона {{ person.garden_zone_usda }}</template>
            </div>
            <div class="masthead__full">{{ fullName }}</div>
          </div>
        </header>

        <hr class="v-rule v-rule--ink" />

        <div v-if="personError" class="error">
          гостья #{{ personId }} не найдена
        </div>
        <div v-else-if="recError" class="error">
          оракулы не свелись: {{ recError.message }}
        </div>
        <div v-else class="layout">
          <!-- main -->
          <section class="main">
            <div class="main__head">
              <div>
                <div class="main__eyebrow">tabula plantarum</div>
                <h2 class="main__title">Свод растений</h2>
              </div>
              <div class="main__hint">
                отметьте 3–5 в&nbsp;избранное и&nbsp;выберите главное дерево
              </div>
            </div>

            <div v-if="pending" class="loading">сводим…</div>

            <div v-else-if="result && result.pool.length === 0" class="empty">
              ни один оракул не дал голоса. проверьте дату рождения или фильтры.
            </div>

            <template v-else-if="result">
              <div class="filter-state" :class="{ 'filter-state--off': !result.filters_applied }">
                <div class="filter-state__main">
                  <span class="filter-state__label">
                    {{ result.filters_applied ? 'свод отфильтрован под участок' : 'свод показан как есть' }}
                  </span>
                  <span class="filter-state__num">
                    <template v-if="result.filters_applied">
                      <template v-if="(result.excluded?.length ?? 0) > 0">скрыто {{ result.excluded.length }}</template>
                      <template v-else>исключений нет</template>
                    </template>
                    <template v-else-if="lastExcludedCount > 0">+{{ lastExcludedCount }} за пределами зоны</template>
                    <template v-else>сырой пул</template>
                  </span>
                </div>
                <button
                  type="button"
                  class="filter-state__toggle"
                  @click="applyFilters = !applyFilters"
                >
                  {{ result.filters_applied ? 'снять фильтр' : '↺ вернуть фильтр' }}
                </button>
              </div>

              <section class="section section--electa">
                <header class="section__head">
                  <div class="section__eyebrow">electa</div>
                  <h3 class="section__title">Избранные</h3>
                  <div class="section__hint">с&nbsp;заметкой эксперта — пойдут в&nbsp;лист гостьи и&nbsp;PDF</div>
                </header>
                <div v-if="electaList.length === 0" class="section__empty">
                  ещё ни&nbsp;одного. отметьте чекбоксом «в&nbsp;избранное» на&nbsp;карточке ниже.
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
                  <div class="section__eyebrow">silva</div>
                  <h3 class="section__title">Резерв</h3>
                  <div class="section__hint">остальной пул, отсортирован по&nbsp;весу</div>
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
            </template>
          </section>

          <!-- side -->
          <aside class="side" v-if="result">
            <div class="v-aside curated-summary">
              <div class="aside__eyebrow">collectio</div>
              <div class="aside__title">Кураторская сборка</div>
              <div class="curated-summary__count">
                <strong>{{ curatedCount }}</strong> в избранном
                <span v-if="titleSlug">· главное: <em>{{ titleSlug }}</em></span>
              </div>

              <label class="notes">
                <span class="notes__label">заметки эксперта</span>
                <textarea
                  v-model="expertNotes"
                  class="notes__area"
                  rows="3"
                  placeholder="комментарий к листу гостьи…"
                />
              </label>

              <button
                class="v-btn save-btn"
                type="button"
                :disabled="saving"
                @click="saveAndOpenClient"
              >
                {{ saving ? 'сохраняем…' : 'сохранить и открыть лист гостьи →' }}
              </button>
              <div v-if="saveError" class="save-error">{{ saveError }}</div>
            </div>

            <div v-if="history.length > 1" class="v-aside history">
              <div class="aside__eyebrow">historiae</div>
              <div class="aside__title">Версии подбора</div>
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
                    <span
                      v-if="h.is_final"
                      class="history__badge history__badge--final"
                      title="версия отдана гостье"
                    >finalis</span>
                  </div>
                  <div class="history__summary">
                    <span v-if="h.title_plant_slug">главное: <em>{{ h.title_plant_slug }}</em> · </span>
                    <span>{{ h.curated_pool?.length ?? 0 }} в избр.</span>
                  </div>

                  <div v-if="i !== 0" class="history__diff">
                    <template v-if="diffAgainstCurrent(h).unchanged">
                      <span class="history__diff-empty">≡ совпадает с текущей</span>
                    </template>
                    <template v-else>
                      <span
                        v-for="slug in diffAgainstCurrent(h).added"
                        :key="`a-${slug}`"
                        class="history__diff-add"
                        :title="`появится в избранном при форке`"
                      >+ {{ slug }}</span>
                      <span
                        v-for="slug in diffAgainstCurrent(h).removed"
                        :key="`r-${slug}`"
                        class="history__diff-rm"
                        :title="`будет снято с избранного при форке`"
                      >− {{ slug }}</span>
                      <span
                        v-if="diffAgainstCurrent(h).titleChanged"
                        class="history__diff-title"
                        :title="`главное дерево сменится`"
                      >
                        →
                        <em>{{ diffAgainstCurrent(h).titleChanged.to || '—' }}</em>
                      </span>
                    </template>
                  </div>

                  <div class="history__buttons">
                    <button
                      type="button"
                      class="v-btn--link history__load"
                      title="подгрузить эту версию в форму — кнопка «сохранить» создаст новую версию из этого набора"
                      @click="loadVersion(h)"
                    >↘ форкнуть</button>
                    <button
                      v-if="!h.is_final"
                      type="button"
                      class="v-btn--link history__finalize"
                      title="пометить финальной — той, что отдана гостье"
                      @click="finalizeVersion(h)"
                    >✦ финальная</button>
                  </div>
                </li>
              </ul>
            </div>

            <div class="v-aside fontes">
              <div class="aside__eyebrow">fontes</div>
              <div class="aside__title">Источники</div>
              <ul class="oracle-list">
                <li
                  v-for="o in allOracles || []"
                  :key="o.id"
                  class="oracle-list__row"
                  :class="{
                    'oracle-list__row--disabled': disabledOracles.has(o.id) || !o.active || !o.implemented,
                  }"
                >
                  <label class="oracle-list__label">
                    <input
                      type="checkbox"
                      :checked="!disabledOracles.has(o.id) && o.active && o.implemented"
                      :disabled="!o.implemented || !o.active"
                      @change="toggleOracleDisabled(o.id)"
                    />
                    <span class="oracle-list__name">{{ o.id }}</span>
                  </label>
                  <span v-if="!o.implemented" class="oracle-list__status" title="оракул в роадмапе, ещё не написан">⏸</span>
                  <span v-else-if="!o.active" class="oracle-list__status" title="отключён в БД через oracles.active=0">×</span>
                </li>
              </ul>
              <transition name="fontes-flash">
                <div v-if="recomputeFlash" class="fontes__flash">свод пересчитан…</div>
              </transition>
            </div>

            <div v-if="result.excluded.length" class="v-aside v-aside--soft excluded">
              <div class="aside__eyebrow">exclusi</div>
              <div class="aside__title">Исключены</div>
              <div v-for="ex in result.excluded" :key="ex.plant_slug" class="excluded__row">
                <div class="excluded__name">{{ ex.plant_slug }}</div>
                <div class="excluded__reason">{{ ex.reason }}</div>
              </div>
              <button
                type="button"
                class="excluded__restore"
                @click="applyFilters = false"
                title="снять фильтр целиком — вернуть все исключённые в свод"
              >↺ вернуть все</button>
            </div>
          </aside>
        </div>

        <footer class="footer">
          <NuxtLink to="/" class="v-btn--link">← к реестру</NuxtLink>
          <span class="footer__note">folium II · expertus</span>
          <button class="v-btn--link" type="button" @click="refresh()">↻ пересобрать</button>
        </footer>
      </div>
    </div>
  </main>
</template>

<style scoped>
.masthead {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: flex-end;
}
.masthead__symbols {
  color: var(--terra);
  font-size: 16px;
  letter-spacing: 6px;
  margin-bottom: 4px;
}
.masthead__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 36px;
  line-height: 1;
  margin: 0;
  color: var(--ink);
}
.masthead__sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 4px;
}
.masthead__right { text-align: right; }
.masthead__for {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
}
.masthead__name {
  font-family: var(--display);
  font-size: 26px;
  line-height: 1;
  color: var(--ink);
  margin-top: 4px;
}
.masthead__meta,
.masthead__full {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 4px;
}
.masthead__full { font-style: italic; }

.layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 32px;
  margin-top: 8px;
}

.main__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 14px;
}
.main__eyebrow {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
}
.main__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 28px;
  line-height: 1;
  margin: 4px 0 0;
  color: var(--ink);
}
.main__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  text-align: right;
  max-width: 220px;
}

.loading, .empty, .error {
  font-family: var(--serif);
  font-style: italic;
  font-size: 16px;
  color: var(--ink-faded);
  padding: 24px 0;
}
.error { color: var(--terra); }

.filter-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 14px;
  margin: 0 0 6px;
  border-left: 4px solid var(--terra);
  background: rgba(139, 58, 31, 0.06);
}
.filter-state--off {
  border-left-color: var(--gold, #b08d44);
  background: rgba(176, 141, 68, 0.12);
}
.filter-state__main {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.filter-state__label {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink);
}
.filter-state__num {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
}
.filter-state--off .filter-state__num { color: #7a5e22; }
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

.section { margin-top: 18px; }
.section:first-of-type { margin-top: 8px; }
.section__head {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: baseline;
  gap: 12px;
  border-top: 1px solid var(--rule);
  padding-top: 10px;
  margin-bottom: 10px;
}
.section--electa .section__head { border-top: 2px solid var(--terra); }
.section__eyebrow {
  grid-row: 1;
  grid-column: 1;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--terra);
}
.section__title {
  grid-row: 2;
  grid-column: 1;
  font-family: var(--display);
  font-weight: 400;
  font-size: 22px;
  line-height: 1;
  margin: 4px 0 0;
  color: var(--ink);
}
.section__hint {
  grid-row: 1 / 3;
  grid-column: 2;
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  text-align: right;
  max-width: 220px;
  align-self: end;
}
.section__empty {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  padding: 12px 14px;
  background: var(--paper-deep);
  border-left: 2px dotted var(--rule);
}

.aside__eyebrow {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--terra);
  margin-bottom: 4px;
}
.aside__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 18px;
  line-height: 1;
  color: var(--ink);
  margin-bottom: 10px;
}

.curated-summary__count {
  font-family: var(--serif);
  font-size: 15px;
  color: var(--ink);
  margin-bottom: 12px;
}
.curated-summary__count strong {
  font-family: var(--display);
  font-size: 18px;
}
.curated-summary__count em {
  color: var(--terra);
  font-style: italic;
}

.notes {
  display: block;
  margin-bottom: 12px;
}
.notes__label {
  display: block;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 4px;
}
.notes__area {
  width: 100%;
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  color: var(--ink);
  background: var(--paper-deep);
  border: 1px solid var(--rule);
  padding: 8px 10px;
  resize: vertical;
  outline: none;
}
.notes__area:focus { border-color: var(--terra); }

.save-btn { width: 100%; padding: 14px 16px; }
.save-error {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
  margin-top: 8px;
}

.oracle-list { list-style: none; margin: 0; padding: 0; }
.oracle-list__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-family: var(--serif);
  font-size: 14px;
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
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
}
.oracle-list__label input { cursor: inherit; }
.oracle-list__label input:disabled { cursor: not-allowed; }
.oracle-list__name { font-family: var(--serif); }
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
.fontes-flash-enter-active,
.fontes-flash-leave-active {
  transition: opacity 0.4s ease;
}
.fontes-flash-enter-from,
.fontes-flash-leave-to { opacity: 0; }

.filters__toggle {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-family: var(--serif);
  font-size: 15px;
  color: var(--ink);
  cursor: pointer;
}
.filters__toggle input { margin-top: 4px; }
.filters__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 8px;
}

.history__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.history__row {
  border-bottom: 1px dotted var(--rule);
  padding-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.history__row:last-child { border-bottom: none; }
.history__row--current { background: var(--paper-deep); padding: 6px 8px; }
.history__meta {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 6px;
}
.history__date {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink);
}
.history__badge {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
}
.history__badge--final {
  margin-left: 6px;
  padding: 1px 6px;
  background: var(--terra);
  color: var(--paper);
}
.history__buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 4px;
}
.history__finalize {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold, #b08d44);
  background: none;
  border: none;
  cursor: pointer;
}
.history__finalize:hover { color: var(--terra); }
.history__summary {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}
.history__summary em { color: var(--terra); }
.history__load {
  align-self: flex-end;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 0;
}
.history__load:hover { color: var(--ink); }

.history__diff {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 6px;
  margin-top: 4px;
  font-family: var(--sans);
  font-size: 10px;
  letter-spacing: 0.04em;
}
.history__diff-add { color: #2da44e; }
.history__diff-rm  { color: #d4380d; text-decoration: line-through; text-decoration-color: rgba(212,56,13,0.5); }
.history__diff-title {
  color: var(--terra);
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  letter-spacing: 0;
}
.history__diff-title em { font-style: italic; color: var(--ink); }
.history__diff-empty {
  color: var(--ink-faded);
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  letter-spacing: 0;
}

.excluded__row { margin-bottom: 8px; }
.excluded__row:last-child { margin-bottom: 0; }
.excluded__name {
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  color: var(--ink);
  text-decoration: line-through;
  text-decoration-color: var(--terra);
}
.excluded__reason {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 2px;
}
.excluded__restore {
  margin-top: 10px;
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 0;
}
.excluded__restore:hover { color: var(--ink); }

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 22px;
  padding-top: 14px;
  border-top: 1px solid var(--ink);
}
.footer__note {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}

@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .masthead { grid-template-columns: 1fr; }
  .masthead__right { text-align: left; }
}
</style>
