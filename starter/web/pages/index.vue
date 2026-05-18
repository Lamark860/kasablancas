<script setup lang="ts">
import type { EyeColor, GeocodeCandidate, PoolEntry, PersonInput, LeadCreate, LeadCompanion } from '~/composables/useApi'

const api = useApi()

const form = reactive({
  first_name: '',
  birth_date: '',
  birth_place: '',
  birth_lat: null as number | null,
  birth_lon: null as number | null,
  birth_tz: null as string | null,
  eye_color: null as EyeColor | null,
})

const submitting = ref(false)
const errorMsg = ref<string | null>(null)

type Step = 'form' | 'result'
const step = ref<Step>('form')

const mainPlant = ref<PoolEntry | null>(null)
const companions = ref<PoolEntry[]>([])

const wantConsult = ref(false)
const contact = ref('')
const leadSubmitting = ref(false)
const leadDone = ref(false)
const leadStubMsg = ref<string | null>(null)

// ── Геокодинг места рождения (логика повторяет intake.vue F1) ───────
type GeoStatus = 'idle' | 'searching' | 'one' | 'many' | 'not_found' | 'error'
const geoStatus = ref<GeoStatus>('idle')
const geoCandidates = ref<GeocodeCandidate[]>([])
const geoSelectedIdx = ref<number | null>(null)
let lastSearched = ''
const originalQuery = ref('')

const geoSelected = computed<GeocodeCandidate | null>(() => {
  if (geoSelectedIdx.value === null) return null
  return geoCandidates.value[geoSelectedIdx.value] ?? null
})

const placeNeedsResolution = computed(() => {
  return !!form.birth_place?.trim() && geoSelected.value === null
})

async function searchPlace() {
  const q = form.birth_place?.trim() ?? ''
  if (!q) {
    geoStatus.value = 'idle'
    geoCandidates.value = []
    geoSelectedIdx.value = null
    lastSearched = ''
    return
  }
  if (q === lastSearched && geoStatus.value !== 'idle') return
  lastSearched = q
  originalQuery.value = q
  geoStatus.value = 'searching'
  geoSelectedIdx.value = null
  try {
    const candidates = await api.searchPlaces(q, 5)
    geoCandidates.value = candidates
    if (candidates.length === 0) {
      geoStatus.value = 'not_found'
    } else if (candidates.length === 1) {
      geoStatus.value = 'one'
      geoSelectedIdx.value = 0
    } else {
      geoStatus.value = 'many'
    }
  } catch {
    geoStatus.value = 'error'
    geoCandidates.value = []
  }
}

function onPlaceBlur() { searchPlace() }
function onPlaceInput() {
  if (form.birth_place?.trim() !== lastSearched) {
    geoStatus.value = 'idle'
    geoCandidates.value = []
    geoSelectedIdx.value = null
  }
}

function shortenTail(s: string): string {
  const notCyr = '(?<![а-яёА-ЯЁ])'
  const notCyrEnd = '(?![а-яёА-ЯЁ])'
  return s
    .replace(/муниципальный округ/gi, 'мун. округ')
    .replace(/городской округ/gi, 'гор. округ')
    .replace(/сельское поселение/gi, 'с/п')
    .replace(/муниципальный район/gi, 'мун. р-н')
    .replace(new RegExp(`${notCyr}район${notCyrEnd}`, 'gi'), 'р-н')
    .replace(new RegExp(`${notCyr}область${notCyrEnd}`, 'gi'), 'обл.')
    .replace(new RegExp(`${notCyr}край${notCyrEnd}`, 'gi'), 'кр.')
    .replace(new RegExp(`${notCyr}республика${notCyrEnd}`, 'gi'), 'респ.')
    .replace(new RegExp(`${notCyr}федеральный округ${notCyrEnd}`, 'gi'), 'фед. округ')
}

function splitLabel(label: string): { name: string; district: string; country: string } {
  const parts = (label || '').split(',').map(s => s.trim()).filter(Boolean)
  if (parts.length === 0) return { name: '—', district: '', country: '' }
  if (parts.length === 1) return { name: parts[0], district: '', country: '' }
  if (parts.length === 2) return { name: parts[0], district: '', country: parts[1] }
  const name = parts[0]
  const country = parts[parts.length - 1]
  const district = shortenTail(parts.slice(1, -1).join(', '))
  return { name, district, country }
}

function pickRegion(inner: string[]): string {
  const cyrRe = /(?<![а-яёА-ЯЁ])(область|край|респ(ублика)?)(?![а-яёА-ЯЁ])/i
  const latRe = /\b(state|county|province|provincia|prefecture)\b/i
  for (let i = 1; i < inner.length; i++) {
    if (cyrRe.test(inner[i]) || latRe.test(inner[i])) return inner[i]
  }
  return inner[inner.length - 1] || ''
}

function formatPicked(c: GeocodeCandidate, fallback: string): string {
  const parts = (c.label || '').split(',').map(s => s.trim()).filter(Boolean)
  if (parts.length === 0) return fallback
  if (parts.length === 1) return parts[0]
  const name = parts[0]
  const inner = parts.slice(1, -1)
  if (inner.length === 0) return name
  const district = inner[0]
  const region = pickRegion(inner)
  const tail = district === region ? district : `${district}, ${region}`
  return shortenTail(`${name} · ${tail}`)
}

function pickCandidate(i: number) {
  const c = geoCandidates.value[i]
  if (!c) return
  geoSelectedIdx.value = i
  geoStatus.value = 'one'
  const formatted = formatPicked(c, form.birth_place || '')
  form.birth_place = formatted
  lastSearched = formatted
}

async function searchAgain() {
  if (originalQuery.value) {
    form.birth_place = originalQuery.value
  }
  lastSearched = ''
  geoStatus.value = 'idle'
  await searchPlace()
}

const eyeColors: { value: EyeColor; label: string }[] = [
  { value: 'blue',  label: 'голубые' },
  { value: 'grey',  label: 'серые' },
  { value: 'green', label: 'зелёные' },
  { value: 'hazel', label: 'ореховые' },
  { value: 'brown', label: 'карие' },
  { value: 'amber', label: 'янтарные' },
  { value: 'dark',  label: 'тёмные' },
]

const canSubmit = computed(() =>
  form.first_name.trim().length >= 2 &&
  !!form.birth_date &&
  !!form.eye_color &&
  !placeNeedsResolution.value
)

const COMPANIONS_LIMIT = 5

async function submit() {
  if (!canSubmit.value) return
  errorMsg.value = null
  submitting.value = true
  try {
    const sel = geoSelected.value
    // Записываем lat/lon/tz обратно в form — чтобы submitLead мог их подобрать,
    // не дёргая geoSelected (которое может уже не существовать, если форма не показана).
    form.birth_lat = sel ? sel.lat : null
    form.birth_lon = sel ? sel.lon : null
    form.birth_tz  = sel ? sel.tz  : null
    const personPayload: PersonInput = {
      first_name: form.first_name.trim(),
      birth_date: form.birth_date,
      eye_color: form.eye_color,
      birth_place: form.birth_place.trim() || null,
      birth_lat: form.birth_lat,
      birth_lon: form.birth_lon,
      birth_tz:  form.birth_tz,
    }
    const out = await api.recommendInline(personPayload)
    if (!out.pool.length) {
      errorMsg.value = 'не удалось подобрать дерево — попробуйте уточнить дату или место рождения'
      return
    }
    const [first, ...rest] = out.pool
    mainPlant.value = first
    companions.value = rest.slice(0, COMPANIONS_LIMIT)
    step.value = 'result'
    // на всякий — сразу промотать к началу страницы (на узких экранах форма ниже шапки)
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e: any) {
    errorMsg.value = e?.data?.detail ? JSON.stringify(e.data.detail) : (e?.message || 'неизвестная ошибка')
  } finally {
    submitting.value = false
  }
}

// Из строки места рождения («Москва · Центральный фед. округ») вытащить
// первую часть — собственно город. Для аналитики «откуда заявки» — этого хватит.
function extractCity(place: string | null | undefined): string | null {
  if (!place) return null
  const head = place.split(/[·,]/)[0]?.trim()
  return head || null
}

async function submitLead() {
  if (!contact.value.trim() || !mainPlant.value) return
  leadStubMsg.value = null
  leadSubmitting.value = true
  try {
    const companionsSnap: LeadCompanion[] = companions.value.map(c => ({
      slug: c.plant_slug,
      name_ru: c.plant_name_ru ?? null,
      match_count: c.match_count ?? null,
    }))
    const payload: LeadCreate = {
      contact: contact.value.trim(),
      want_consultation: true,
      first_name: form.first_name.trim(),
      birth_date: form.birth_date,
      birth_place: form.birth_place.trim() || null,
      birth_lat: form.birth_lat,
      birth_lon: form.birth_lon,
      birth_tz: form.birth_tz,
      eye_color: form.eye_color,
      main_plant_slug: mainPlant.value.plant_slug,
      main_plant_name: mainPlant.value.plant_name_ru ?? mainPlant.value.plant_slug,
      companions: companionsSnap,
      city: extractCity(form.birth_place),
      source: typeof document !== 'undefined' && document.referrer
        ? { referrer: document.referrer }
        : null,
    }
    await api.createLead(payload)
    leadDone.value = true
  } catch (e: any) {
    leadStubMsg.value = e?.data?.detail
      ? JSON.stringify(e.data.detail)
      : (e?.message || 'не удалось отправить — попробуйте ещё раз')
  } finally {
    leadSubmitting.value = false
  }
}

function reset() {
  step.value = 'form'
  mainPlant.value = null
  companions.value = []
  wantConsult.value = false
  contact.value = ''
  leadDone.value = false
  leadStubMsg.value = null
}

function reasonsFor(entry: PoolEntry): string[] {
  // Берём краткие причины для клиента из тех источников, у которых есть текст.
  return entry.sources
    .map(s => s.reason_for_client || s.reason_for_expert)
    .filter(Boolean)
}

const firstName = computed(() => form.first_name.trim() || 'госпожа')
const mainReasons = computed<string[]>(() =>
  mainPlant.value ? reasonsFor(mainPlant.value) : []
)
const mainName = computed(() =>
  mainPlant.value ? (mainPlant.value.plant_name_ru || mainPlant.value.plant_slug) : ''
)
</script>

<template>
  <main class="v-page v-page--narrow">
    <div class="v-sheet v-grain">
      <div class="v-frame">
        <header v-if="step === 'form'" class="masthead">
          <div class="masthead__eyebrow">Hortus Animæ</div>
          <h1 class="masthead__title">Узнайте своё тотемное дерево</h1>
          <div class="masthead__sub">
            короткая анкета — мы сведём друидский календарь, зодиак, нумерологию имени
            и цвет ваших глаз, и расскажем, какое дерево ваше и какие растения его поддерживают
          </div>
        </header>

        <header v-else class="masthead">
          <div class="masthead__eyebrow">Hortus Animæ · ваше дерево</div>
          <h1 class="masthead__title">{{ firstName }}, ваше дерево</h1>
          <div class="masthead__sub">
            собрано на пересечении друидского календаря, зодиака,
            нумерологии имени и цвета ваших глаз
          </div>
        </header>

        <hr class="v-rule v-rule--ink" />

        <form v-if="step === 'form'" class="form" @submit.prevent="submit">
          <div class="field">
            <div class="v-field-label">Имя</div>
            <input
              v-model="form.first_name"
              class="v-input"
              placeholder="как вас называть"
              required
            />
          </div>

          <div class="field">
            <div class="v-field-label">Дата рождения</div>
            <input
              v-model="form.birth_date"
              class="v-input"
              type="date"
              required
            />
          </div>

          <div class="field place">
            <div class="v-field-label">
              Место рождения
              <button
                v-if="geoStatus === 'one'"
                type="button"
                class="place__retry"
                :disabled="geoStatus === 'searching'"
                @click="searchAgain"
              >↻ найти заново</button>
            </div>
            <input
              v-model="form.birth_place"
              class="v-input"
              :class="{ 'v-input--error': geoStatus === 'not_found' || geoStatus === 'error' }"
              placeholder="Санкт-Петербург"
              @blur="onPlaceBlur"
              @input="onPlaceInput"
            />

            <div v-if="geoStatus === 'searching'" class="place__hint">ищу координаты…</div>

            <div v-if="geoStatus === 'one' && geoSelected" class="place__meta">
              <span class="place__meta-coords">{{ geoSelected.lat.toFixed(2) }}, {{ geoSelected.lon.toFixed(2) }}</span>
              <span v-if="geoSelected.tz" class="place__meta-sep">·</span>
              <span v-if="geoSelected.tz" class="place__meta-tz">{{ geoSelected.tz }}</span>
              <span class="place__meta-mark" aria-hidden="true">❦</span>
            </div>

            <div v-if="geoStatus === 'not_found'" class="place__error">
              место не найдено — проверьте написание или сотрите поле, если место неизвестно
            </div>

            <div v-if="geoStatus === 'error'" class="place__error">
              геокодер недоступен — можно оставить пустым, асцендент тогда не посчитается
            </div>

            <div class="field__hint">
              если не уверены — можно пропустить, подбор всё равно состоится
              по дате рождения, имени и цвету глаз
            </div>
          </div>

          <div v-if="geoStatus === 'many'" class="place__many">
            <div class="place__many-label">найдено {{ geoCandidates.length }} — выберите один:</div>
            <ul class="place__many-list">
              <li
                v-for="(c, i) in geoCandidates"
                :key="`${c.lat}-${c.lon}`"
                class="place__candidate"
                :class="{ 'place__candidate--active': geoSelectedIdx === i }"
                :title="c.label || form.birth_place"
                @click="pickCandidate(i)"
              >
                <span class="place__candidate-mark" aria-hidden="true">◆</span>
                <div class="place__candidate-body">
                  <div class="place__candidate-line1">
                    <span class="place__candidate-name">{{ splitLabel(c.label || form.birth_place).name }}</span>
                    <span
                      v-if="splitLabel(c.label || '').district"
                      class="place__candidate-district"
                    >· {{ splitLabel(c.label || '').district }}</span>
                  </div>
                  <div class="place__candidate-line2">
                    <span v-if="splitLabel(c.label || '').country">{{ splitLabel(c.label || '').country }} · </span>
                    <span class="place__candidate-coords">{{ c.lat.toFixed(2) }}, {{ c.lon.toFixed(2) }}</span>
                  </div>
                </div>
              </li>
            </ul>
            <div class="place__many-foot">
              не нашли нужного — сотрите поле, асцендент тогда не посчитается
            </div>
          </div>

          <div class="field">
            <div class="v-field-label">
              Цвет глаз
              <em v-if="form.eye_color" class="field-aux">
                {{ eyeColors.find(c => c.value === form.eye_color)?.label }}
              </em>
            </div>
            <div class="swatches">
              <button
                v-for="c in eyeColors"
                :key="c.value"
                type="button"
                class="swatch"
                :class="[`swatch--${c.value}`, { 'swatch--active': form.eye_color === c.value }]"
                :title="c.label"
                :aria-label="c.label"
                @click="form.eye_color = form.eye_color === c.value ? null : c.value"
              >
                <span class="swatch__dot" aria-hidden="true"></span>
              </button>
            </div>
          </div>

          <div v-if="errorMsg" class="info">{{ errorMsg }}</div>

          <footer class="form__footer">
            <button
              type="submit"
              class="form__primary"
              :disabled="!canSubmit || submitting"
            >
              {{ submitting ? 'сводим источники…' : '✦ узнать своё дерево ✦' }}
            </button>
            <div class="form__note">это бесплатно</div>
          </footer>
        </form>

        <section v-else-if="mainPlant" class="result">
          <article class="main-tree">
            <div class="main-tree__eyebrow">главное</div>
            <div class="main-tree__circle" aria-hidden="true">
              <span class="main-tree__letter">{{ mainName[0] }}</span>
            </div>
            <h2 class="main-tree__name">{{ mainName }}</h2>
            <p v-if="mainPlant.plant_short_story" class="main-tree__story">
              «{{ mainPlant.plant_short_story }}»
            </p>
            <ul v-if="mainReasons.length" class="main-tree__reasons">
              <li v-for="(r, i) in mainReasons" :key="i">{{ r }}</li>
            </ul>
          </article>

          <section v-if="companions.length" class="others">
            <div class="others__eyebrow">его сопровождают</div>
            <div class="others__grid">
              <div
                v-for="c in companions"
                :key="c.plant_slug"
                class="other"
              >
                <div class="other__name">{{ c.plant_name_ru || c.plant_slug }}</div>
                <div v-if="c.plant_short_story" class="other__story">{{ c.plant_short_story }}</div>
              </div>
            </div>
          </section>

          <hr class="v-rule" />

          <section class="consult">
            <label class="consult__check">
              <input type="checkbox" v-model="wantConsult" />
              <span>хочу подробную консультацию</span>
            </label>

            <div v-if="wantConsult && !leadDone" class="consult__form">
              <p class="consult__hint">
                оставьте телеграм или телефон — наш эксперт свяжется и подскажет,
                как именно посадить ваше дерево, в какой период и что положить рядом
              </p>
              <div class="field">
                <div class="v-field-label">Телеграм / телефон</div>
                <input
                  v-model="contact"
                  class="v-input"
                  placeholder="@username или +7…"
                />
              </div>

              <div v-if="leadStubMsg" class="info">{{ leadStubMsg }}</div>

              <button
                type="button"
                class="form__primary"
                :disabled="!contact.trim() || leadSubmitting"
                @click="submitLead"
              >
                {{ leadSubmitting ? 'отправляем…' : '✦ связаться со мной ✦' }}
              </button>
            </div>

            <div v-if="leadDone" class="lead-done">
              ✦ принято — мы скоро вам напишем
            </div>
          </section>

          <footer class="result-footer">
            <button type="button" class="v-btn--link result-footer__back" @click="reset">
              ← начать заново
            </button>
          </footer>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped>
.masthead {
  text-align: center;
  margin-bottom: 16px;
}
.masthead__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--terra);
}
.masthead__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 36px;
  line-height: 1.15;
  margin: 12px 0 10px;
  color: var(--ink);
}
.masthead__sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  line-height: 1.6;
  max-width: 480px;
  margin: 0 auto;
}

.form { margin-top: 22px; }
.field { margin-bottom: 18px; }

.v-field-label {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faded);
  margin-bottom: 8px;
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.field-aux {
  font-family: var(--serif);
  font-style: italic;
  text-transform: none;
  letter-spacing: 0;
  font-size: 13px;
  color: var(--ink);
}
.field__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 12px;
  color: var(--ink-faded);
  margin-top: 6px;
}

/* — Свотчи цвета глаз — */
.swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.swatch {
  width: 36px;
  height: 36px;
  padding: 0;
  background: transparent;
  border: 1px solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.swatch:hover { border-color: var(--rule); }
.swatch--active { border-color: var(--ink); }
.swatch__dot {
  display: block;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
}
.swatch--active .swatch__dot {
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.4), 0 0 0 2px var(--paper), 0 0 0 3px var(--ink);
}
.swatch--blue  .swatch__dot { background: #5d8aa8; }
.swatch--grey  .swatch__dot { background: #8a8a8a; }
.swatch--green .swatch__dot { background: #6b8e5a; }
.swatch--hazel .swatch__dot { background: #a87d4a; }
.swatch--brown .swatch__dot { background: #6b4423; }
.swatch--amber .swatch__dot { background: #c08552; }
.swatch--dark  .swatch__dot { background: #2d2218; }

/* — Геокодер места рождения — */
.place__retry {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}
.place__retry:hover { color: var(--ink); }
.place__retry:disabled { opacity: 0.4; cursor: wait; }
.v-input--error { border-color: var(--terra); }

.place__hint {
  margin-top: 6px;
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}
.place__meta {
  margin-top: 6px;
  display: flex;
  align-items: baseline;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
}
.place__meta-coords,
.place__meta-tz {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--ink-faded);
}
.place__meta-sep {
  color: var(--rule);
  font-family: var(--sans);
  font-size: 11px;
}
.place__meta-mark {
  margin-left: auto;
  color: var(--terra);
  font-family: var(--serif);
  font-size: 14px;
  line-height: 1;
}
.place__error {
  margin-top: 6px;
  padding: 8px 10px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--terra);
  line-height: 1.4;
}
.place__many {
  margin: -10px 0 28px;
  padding: 12px 16px 8px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
}
.place__many-label {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 8px;
}
.place__many-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
.place__candidate {
  display: grid;
  grid-template-columns: 14px 1fr;
  gap: 10px;
  align-items: start;
  padding: 10px 8px;
  cursor: pointer;
  min-width: 0;
  transition: background 0.12s ease;
}
.place__candidate:hover { background: rgba(139, 58, 31, 0.06); }
.place__candidate--active { background: rgba(139, 58, 31, 0.1); }
.place__candidate-mark {
  color: var(--rule);
  font-size: 10px;
  line-height: 1.6;
  text-align: center;
  transition: color 0.15s ease;
}
.place__candidate:hover .place__candidate-mark { color: var(--ink); }
.place__candidate--active .place__candidate-mark { color: var(--terra); }
.place__candidate-body { min-width: 0; }
.place__candidate-line1 {
  font-family: var(--serif);
  font-size: 14px;
  line-height: 1.3;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.place__candidate-name { font-weight: 500; }
.place__candidate-district {
  font-style: italic;
  color: var(--ink-faded);
  margin-left: 4px;
}
.place__candidate-line2 {
  font-family: var(--sans);
  font-size: 10px;
  color: var(--ink-faded);
  letter-spacing: 0.04em;
  margin-top: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.place__candidate-coords { font-style: normal; }
.place__many-foot {
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-faded);
  padding: 0 8px 2px;
  margin-top: 18px;
}

.info {
  margin-top: 14px;
  padding: 12px 14px;
  background: var(--paper-deep);
  border: 1px dashed var(--terra);
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
}

.form__footer {
  text-align: center;
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid var(--rule);
}
.form__primary {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  padding: 14px 32px;
  background: var(--ink);
  color: var(--paper);
  border: 1px solid var(--ink);
  cursor: pointer;
}
.form__primary:hover:not(:disabled) {
  background: var(--terra);
  border-color: var(--terra);
}
.form__primary:disabled { opacity: 0.4; cursor: not-allowed; }
.form__note {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 12px;
}

@media (max-width: 640px) {
  .place__many-list { grid-template-columns: 1fr; }
}

/* — Result: главное дерево + сопровождающие — */
.result { margin-top: 18px; }

.main-tree {
  text-align: center;
  padding: 8px 0 24px;
}
.main-tree__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--terra);
  margin-bottom: 18px;
}
.main-tree__circle {
  width: 96px;
  height: 96px;
  margin: 0 auto 16px;
  border-radius: 50%;
  border: 1.5px solid var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--paper);
}
.main-tree__letter {
  font-family: var(--display);
  font-size: 48px;
  line-height: 1;
  color: var(--ink);
}
.main-tree__name {
  font-family: var(--display);
  font-weight: 400;
  font-size: 38px;
  line-height: 1.1;
  margin: 0 0 14px;
  color: var(--ink);
}
.main-tree__story {
  font-family: var(--serif);
  font-style: italic;
  font-size: 16px;
  line-height: 1.6;
  color: var(--ink);
  max-width: 480px;
  margin: 0 auto 16px;
}
.main-tree__reasons {
  list-style: none;
  margin: 12px auto 0;
  padding: 0;
  max-width: 480px;
  text-align: left;
}
.main-tree__reasons li {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  line-height: 1.5;
  padding: 5px 0 5px 18px;
  position: relative;
}
.main-tree__reasons li::before {
  content: "·";
  position: absolute;
  left: 4px;
  color: var(--terra);
  font-weight: 700;
}

.others {
  margin-top: 26px;
  padding-top: 22px;
  border-top: 1px dotted var(--rule);
}
.others__eyebrow {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.32em;
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
  padding: 14px;
  background: var(--paper-deep);
  border: 1px solid var(--rule);
}
.other__name {
  font-family: var(--display);
  font-size: 20px;
  color: var(--ink);
  margin-bottom: 6px;
}
.other__story {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink-faded);
}

.consult {
  margin-top: 28px;
  padding-top: 18px;
}
.consult__check {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-family: var(--serif);
  font-style: italic;
  font-size: 16px;
  color: var(--ink);
  padding: 8px 0;
}
.consult__check input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--terra);
  cursor: pointer;
}
.consult__form {
  margin-top: 14px;
  padding: 16px 18px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
  text-align: center;
}
.consult__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  line-height: 1.6;
  margin: 0 0 14px;
  max-width: 440px;
  margin-left: auto;
  margin-right: auto;
}
.consult__form .field { text-align: left; max-width: 360px; margin: 0 auto 14px; }
.lead-done {
  margin-top: 14px;
  padding: 14px;
  background: var(--paper-deep);
  border-left: 2px solid var(--terra);
  font-family: var(--serif);
  font-style: italic;
  font-size: 15px;
  color: var(--terra);
  text-align: center;
}

.result-footer {
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid var(--rule);
  text-align: center;
}
.result-footer__back {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px 0;
}

@media (max-width: 540px) {
  .others__grid { grid-template-columns: 1fr; }
}
</style>
