<script setup lang="ts">
import type { PersonInput, EyeColor, Gender, GardenSoil, GardenSun, GeocodeCandidate } from '~/composables/useApi'

const api = useApi()
const router = useRouter()

const form = reactive<PersonInput>({
  first_name: '',
  middle_name: '',
  last_name: '',
  gender: null,
  birth_date: '',
  birth_time: '',
  birth_place: '',
  eye_color: null,
  garden_zone_usda: null,
  garden_region: '',
  garden_soil: null,
  garden_sun: null,
})

const submitting = ref(false)
const errorMsg = ref<string | null>(null)

// ── Геокодинг места рождения (F1: blur-валидация) ─────────────────
type GeoStatus = 'idle' | 'searching' | 'one' | 'many' | 'not_found' | 'error'
const geoStatus = ref<GeoStatus>('idle')
const geoCandidates = ref<GeocodeCandidate[]>([])
const geoSelectedIdx = ref<number | null>(null)
let lastSearched = ''
// Что юзер реально напечатал до выбора — чтобы «↻ найти заново» искал по нему,
// а не по отформатированной строке, которую мы кладём в инпут после pickCandidate.
const originalQuery = ref('')

const geoSelected = computed<GeocodeCandidate | null>(() => {
  if (geoSelectedIdx.value === null) return null
  return geoCandidates.value[geoSelectedIdx.value] ?? null
})

const placeNeedsResolution = computed(() => {
  // Эксперт ввёл место, но кандидата ещё не выбрал → submit заблокирован.
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
  if (q === lastSearched && geoStatus.value !== 'idle') return  // не дёргаем повторно если ничего не изменилось
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

function onPlaceBlur() {
  searchPlace()
}
function onPlaceInput() {
  // редактирование — сбрасываем выбор и предыдущие кандидаты, чтобы не вводить в заблуждение
  if (form.birth_place?.trim() !== lastSearched) {
    geoStatus.value = 'idle'
    geoCandidates.value = []
    geoSelectedIdx.value = null
  }
}
function fmtCoords(c: GeocodeCandidate) {
  return `${c.lat.toFixed(2)} / ${c.lon.toFixed(2)}${c.tz ? ' · ' + c.tz : ''}`
}

// Сокращения для tail-строки в выборе места (даёт воздух).
// ВАЖНО: \b в JS работает только по ASCII-границам, поэтому для кириллицы
// используем lookbehind/lookahead по русским буквам.
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

// Парсим label Nominatim в три части: name / district / country
// "Москва, ЦФО, Россия" → { name: "Москва", district: "ЦФО", country: "Россия" }
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

// Из всего пути Nominatim — выдёргиваем «регион» (область/край/штат/county).
// Если такого нет — последний внутренний элемент (без страны).
// ВАЖНО: \b не работает с кириллицей, поэтому проверяем по lookbehind/lookahead
// (для кириллических токенов) и по \b (для латиницы).
function pickRegion(inner: string[]): string {
  const cyrRe = /(?<![а-яёА-ЯЁ])(область|край|респ(ублика)?)(?![а-яёА-ЯЁ])/i
  const latRe = /\b(state|county|province|provincia|prefecture)\b/i
  for (let i = 1; i < inner.length; i++) {
    if (cyrRe.test(inner[i]) || latRe.test(inner[i])) return inner[i]
  }
  return inner[inner.length - 1] || ''
}

// Формат для инпута после выбора: «Имя · район, регион» (страну убираем — её
// явно избыточно показывать после ручного выбора кандидата).
function formatPicked(c: GeocodeCandidate, fallback: string): string {
  const parts = (c.label || '').split(',').map(s => s.trim()).filter(Boolean)
  if (parts.length === 0) return fallback
  if (parts.length === 1) return parts[0]
  const name = parts[0]
  const inner = parts.slice(1, -1)  // отбрасываем страну
  if (inner.length === 0) return name
  const district = inner[0]
  const region = pickRegion(inner)
  const tail = district === region ? district : `${district}, ${region}`
  return shortenTail(`${name} · ${tail}`)
}

// При выборе кандидата — схлопываем список в одно-кандидатный 'one' state
// и пишем в инпут сокращённую человеко-читаемую версию.
function pickCandidate(i: number) {
  const c = geoCandidates.value[i]
  if (!c) return
  geoSelectedIdx.value = i
  geoStatus.value = 'one'
  const formatted = formatPicked(c, form.birth_place || '')
  form.birth_place = formatted
  // чтобы onPlaceInput не сбросил состояние — синхронизируем lastSearched
  lastSearched = formatted
}

// «↻ найти заново» — возвращаем оригинальный запрос юзера и дёргаем геокодер.
async function searchAgain() {
  if (originalQuery.value) {
    form.birth_place = originalQuery.value
  }
  lastSearched = ''  // снимаем кэш, иначе searchPlace вернётся слишком рано
  geoStatus.value = 'idle'
  await searchPlace()
}

const eyeColors: { value: EyeColor; label: string }[] = [
  { value: 'blue', label: 'голубые' },
  { value: 'grey', label: 'серые' },
  { value: 'green', label: 'зелёные' },
  { value: 'hazel', label: 'ореховые' },
  { value: 'brown', label: 'карие' },
  { value: 'amber', label: 'янтарные' },
  { value: 'dark', label: 'тёмные' },
]

const genders: { value: Gender; label: string }[] = [
  { value: 'female', label: 'женский' },
  { value: 'male',   label: 'мужской' },
  { value: 'other',  label: 'иной' },
]

const sunOpts: { value: GardenSun; label: string }[] = [
  { value: 'sun',        label: 'солнце' },
  { value: 'part_shade', label: 'полутень' },
  { value: 'shade',      label: 'тень' },
  { value: 'mixed',      label: 'смешанно' },
]

const soilOpts: { value: GardenSoil; label: string }[] = [
  { value: 'dry',    label: 'сухая' },
  { value: 'normal', label: 'обычная' },
  { value: 'wet',    label: 'влажная' },
]

const zoneOpts = [
  { v: 3, l: 'зона 3 · север' },
  { v: 4, l: 'зона 4 · Урал' },
  { v: 5, l: 'зона 5 · сев. ср.полоса' },
  { v: 6, l: 'зона 6 · Москва' },
  { v: 7, l: 'зона 7 · Чернозёмье' },
  { v: 8, l: 'зона 8 · Кубань' },
]

async function submit(mode: 'pool' | 'draft' = 'pool') {
  errorMsg.value = null

  if (placeNeedsResolution.value) {
    errorMsg.value = 'место рождения не разрешено: выбери один из вариантов или сотри поле, если не известно'
    return
  }

  submitting.value = true
  try {
    const sel = geoSelected.value
    const payload: PersonInput = {
      ...form,
      middle_name:    form.middle_name    || null,
      last_name:      form.last_name      || null,
      birth_time:     form.birth_time     || null,
      birth_place:    form.birth_place    || null,
      garden_region:  form.garden_region  || null,
      // если эксперт выбрал кандидата — отправляем явные координаты,
      // бэк не будет лезть в Nominatim повторно
      birth_lat:      sel ? sel.lat : null,
      birth_lon:      sel ? sel.lon : null,
      birth_tz:       sel ? sel.tz  : null,
    }
    const created = await api.createPerson(payload)
    // 'draft' → возврат к реестру, эксперт продолжит позже.
    // 'pool'  → сразу к экспертному пулу.
    await router.push(mode === 'draft' ? '/' : `/expert/${created.id}`)
  } catch (e: any) {
    errorMsg.value = e?.data?.detail
      ? JSON.stringify(e.data.detail)
      : (e?.message || 'неизвестная ошибка')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="v-page v-page--narrow">
    <div class="v-sheet v-grain">
      <div class="v-frame">
        <header class="masthead">
          <div class="masthead__eyebrow">folium I · de hospita</div>
          <h1 class="masthead__title">О новой госпоже</h1>
          <div class="masthead__sub">заполняется экспертом, прежде чем сводить источники</div>
        </header>

        <form class="form" @submit.prevent="submit('pool')">

          <div class="row">
            <div class="field">
              <div class="v-field-label">Имя <span class="required">*</span></div>
              <input v-model="form.first_name" class="v-input" placeholder="Ева" required />
            </div>
            <div class="field">
              <div class="v-field-label">Отчество</div>
              <input v-model="form.middle_name" class="v-input" placeholder="—" />
            </div>
            <div class="field">
              <div class="v-field-label">Фамилия</div>
              <input v-model="form.last_name" class="v-input" placeholder="—" />
            </div>
          </div>

          <div class="row row--with-place">
            <div class="field">
              <div class="v-field-label">Дата рождения <span class="required">*</span></div>
              <input v-model="form.birth_date" class="v-input" type="date" required />
            </div>
            <div class="field">
              <div class="v-field-label">Час</div>
              <input v-model="form.birth_time" class="v-input" type="time" />
              <div class="field__hint">если не известен — берётся 12:00, без асцендента</div>
            </div>
            <div class="field place">
              <div class="v-field-label">
                Место
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
                placeholder="Москва"
                @blur="onPlaceBlur"
                @input="onPlaceInput"
              />

              <div v-if="geoStatus === 'searching'" class="place__hint">ищу координаты…</div>

              <!-- Мета под полем: координаты+таймзона моно-шрифтом и винный маркер ❦.
                   Высоту инпута не ломает — живёт как hint, по аналогии с подсказкой под «Час». -->
              <div v-if="geoStatus === 'one' && geoSelected" class="place__meta">
                <span class="place__meta-coords">{{ geoSelected.lat.toFixed(2) }}, {{ geoSelected.lon.toFixed(2) }}</span>
                <span v-if="geoSelected.tz" class="place__meta-sep">·</span>
                <span v-if="geoSelected.tz" class="place__meta-tz">{{ geoSelected.tz }}</span>
                <span class="place__meta-mark" aria-hidden="true">❦</span>
              </div>

              <div v-if="geoStatus === 'not_found'" class="place__error">
                место не найдено — проверь написание или сотри поле, если место неизвестно
              </div>

              <div v-if="geoStatus === 'error'" class="place__error">
                геокодер недоступен — можно сохранить без координат (асцендент тогда не посчитается)
              </div>
            </div>
          </div>

          <!-- Полноширинный блок выбора кандидатов: вне строки, чтобы названия не обрезались. -->
          <div v-if="geoStatus === 'many'" class="place__many">
            <div class="place__many-label">найдено {{ geoCandidates.length }} — выбери один:</div>
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
              не нашёл нужного — сотри поле, асцендент тогда не посчитается
            </div>
          </div>

          <div class="row">
            <div class="field">
              <div class="v-field-label">
                Пол
                <button
                  v-if="form.gender !== null"
                  type="button"
                  class="field-clear"
                  @click="form.gender = null"
                  title="сбросить выбор"
                >× сбросить</button>
              </div>
              <div class="pills">
                <button
                  v-for="g in genders"
                  :key="g.value"
                  type="button"
                  class="pill"
                  :class="{ 'pill--active': form.gender === g.value }"
                  @click="form.gender = form.gender === g.value ? null : g.value"
                >{{ g.label }}</button>
              </div>
            </div>
            <div class="field">
              <div class="v-field-label">
                Взгляд
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
                  @click="form.eye_color = form.eye_color === c.value ? null : c.value"
                  :aria-label="c.label"
                >
                  <span class="swatch__dot" aria-hidden="true"></span>
                </button>
              </div>
            </div>
          </div>

          <fieldset class="v-fieldset garden">
            <div class="v-field-label">Сад</div>

            <div class="row garden__row">
              <div class="field">
                <div class="v-field-label">Регион / участок</div>
                <input v-model="form.garden_region" class="v-input" placeholder="Истринский р-н, ~12 соток" />
              </div>
              <div class="field">
                <div class="v-field-label">USDA-зона</div>
                <select v-model.number="form.garden_zone_usda" class="v-select">
                  <option :value="null">—</option>
                  <option v-for="z in zoneOpts" :key="z.v" :value="z.v">{{ z.l }}</option>
                </select>
              </div>
            </div>

            <div class="row garden__row">
              <div class="field">
                <div class="v-field-label">Свет</div>
                <select v-model="form.garden_sun" class="v-select">
                  <option :value="null">—</option>
                  <option v-for="s in sunOpts" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </div>
              <div class="field">
                <div class="v-field-label">Почва</div>
                <select v-model="form.garden_soil" class="v-select">
                  <option :value="null">—</option>
                  <option v-for="s in soilOpts" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </div>
            </div>
          </fieldset>

          <div v-if="errorMsg" class="error">{{ errorMsg }}</div>

          <footer class="form__footer">
            <NuxtLink to="/" class="v-btn--link form__back">← к&nbsp;реестру</NuxtLink>
            <div class="form__actions">
              <button
                type="button"
                class="form__draft"
                :disabled="submitting || !form.first_name || !form.birth_date"
                title="сохранить и вернуться в реестр — продолжишь позже"
                @click="submit('draft')"
              >сохранить черновик</button>
              <button type="submit" class="form__primary" :disabled="submitting">
                {{ submitting ? 'сводим…' : 'свести источники' }}
              </button>
            </div>
          </footer>
        </form>
      </div>
    </div>
  </main>
</template>

<style scoped>
.masthead {
  text-align: center;
  margin-bottom: 18px;
}
.masthead__eyebrow {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--terra);
}
.masthead__title {
  font-family: var(--display);
  font-weight: 400;
  font-size: 32px;
  line-height: 1;
  margin: 6px 0 0;
  color: var(--ink);
}
.masthead__sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
  margin-top: 6px;
}

.form { margin-top: 16px; }
.v-field-label {
  font-size: 11px;
  letter-spacing: 0.18em;
  margin-bottom: 8px;
}

.field__hint {
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-faded);
  margin-top: 4px;
}

/* — Пол: pill-радио — */
.pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding-top: 2px;
}
.pill {
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--rule);
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pill:hover { border-color: var(--ink); }
.pill--active {
  background: var(--terra);
  border-color: var(--terra);
  color: var(--paper);
}
.pill--active:hover { background: var(--terra-deep, #6e2c15); border-color: var(--terra-deep, #6e2c15); }

.v-field-label {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.field-clear {
  font-family: var(--serif);
  font-style: italic;
  font-size: 11px;
  color: var(--ink-faded);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  letter-spacing: 0;
  text-transform: none;
  font-weight: normal;
}
.field-clear:hover { color: var(--terra); }
.field-aux {
  font-family: var(--serif);
  font-style: italic;
  font-size: 12px;
  letter-spacing: 0;
  text-transform: none;
  color: var(--terra);
  font-weight: normal;
}

/* — Свотчи цвета глаз: только кружок, лейбл через title + field-aux — */
.swatches {
  display: flex;
  gap: 8px;
  padding-top: 2px;
}
.swatch {
  width: 28px;
  height: 28px;
  padding: 0;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.swatch:hover { border-color: var(--rule); }
.swatch--active {
  border-color: var(--terra);
  border-width: 1.5px;
}
.swatch__dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid var(--ink);
  box-shadow: inset 0 0 3px rgba(0, 0, 0, 0.3);
}
.swatch--active .swatch__dot {
  box-shadow: inset 0 0 3px rgba(0, 0, 0, 0.3), 0 0 0 2px var(--paper);
}

.swatch--blue  .swatch__dot { background: #5d8aa8; }
.swatch--grey  .swatch__dot { background: #8a8a8a; }
.swatch--green .swatch__dot { background: #6b8e5a; }
.swatch--hazel .swatch__dot { background: #a87d4a; }
.swatch--brown .swatch__dot { background: #6b4423; }
.swatch--amber .swatch__dot { background: #c08552; }
.swatch--dark  .swatch__dot { background: #2d2218; }

/* — Footer кнопки — */
.form__footer {
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid var(--ink);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.form__back {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  text-decoration: none;
}
.form__back:hover { color: var(--ink); }
.form__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.form__draft {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-faded);
  background: transparent;
  border: 1px dashed var(--rule);
  padding: 8px 14px;
  cursor: pointer;
  white-space: nowrap;
}
.form__draft:hover:not(:disabled) { color: var(--ink); border-color: var(--ink); }
.form__draft:disabled { opacity: 0.4; cursor: not-allowed; }
.form__primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  line-height: 1;
  color: var(--paper);
  background: var(--terra);
  border: 1px solid var(--terra);
  padding: 10px 18px;
  cursor: pointer;
  white-space: nowrap;
  letter-spacing: 0.02em;
}
.form__primary::before {
  content: '✦';
  font-size: 12px;
  line-height: 1;
  opacity: 0.85;
}
.form__primary:hover:not(:disabled) {
  background: var(--terra-deep, #6e2c15);
  border-color: var(--terra-deep, #6e2c15);
}
.form__primary:disabled { opacity: 0.5; cursor: not-allowed; }


.row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
  margin-bottom: 28px;
}
.row:has(> .field:nth-child(2):last-child) { grid-template-columns: 1fr 1fr; }
/* Строка с полем «Место»: даём ему вдвое больше воздуха — Дата/Час короткие
   (10 и 5 символов), а Место может содержать «Имя · район, область» + мета.
   1.2 / 0.8 — чтобы лейбл «Дата рождения» с широким letter-spacing влез в одну строку. */
.row--with-place { grid-template-columns: 1.2fr 0.8fr 2fr; }

.field { display: flex; flex-direction: column; }
.required { color: var(--terra); }

.garden { margin-top: 20px; padding: 18px 20px; }
.garden__row { grid-template-columns: 1fr 1fr; margin-bottom: 20px; gap: 28px; }
.garden__row:last-child { margin-bottom: 0; }

.error {
  margin-top: 14px;
  padding: 10px 14px;
  background: var(--paper-deep);
  border: 1px dashed var(--terra);
  font-family: var(--serif);
  font-style: italic;
  color: var(--terra);
  font-size: 15px;
  overflow-wrap: anywhere;
}

.form__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 36px;
  padding-top: 22px;
  border-top: 1px solid var(--rule);
}

@media (max-width: 640px) {
  .row, .garden__row, .row--with-place { grid-template-columns: 1fr; gap: 14px; }
}

/* ── место рождения / геокод ── */
.place .v-field-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
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

.v-input--error {
  border-color: var(--terra);
}

.place__hint {
  margin-top: 6px;
  font-family: var(--serif);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-faded);
}
/* Компактная мета после успешного выбора: координаты + таймзона + ❦.
   Живёт под линией поля, как технические метаданные. Высоту строки не ломает. */
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
/* Полноширинный блок «найдено N — выбери»: занимает строку целиком,
   кандидаты идут в 2 колонки чтобы не вытягивать форму по вертикали. */
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

@media (max-width: 640px) {
  .place__many-list { grid-template-columns: 1fr; }
}
</style>
