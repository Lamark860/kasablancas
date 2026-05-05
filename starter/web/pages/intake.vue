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

async function submit() {
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
    await router.push(`/expert/${created.id}`)
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

        <form class="form" @submit.prevent="submit">

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

          <div class="row">
            <div class="field">
              <div class="v-field-label">Дата рождения <span class="required">*</span></div>
              <input v-model="form.birth_date" class="v-input" type="date" required />
            </div>
            <div class="field">
              <div class="v-field-label">Час</div>
              <input v-model="form.birth_time" class="v-input" type="time" />
            </div>
            <div class="field place">
              <div class="v-field-label">
                Место
                <button
                  v-if="form.birth_place?.trim()"
                  type="button"
                  class="place__retry"
                  :disabled="geoStatus === 'searching'"
                  @click="searchPlace"
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

              <div v-if="geoStatus === 'one' && geoSelected" class="place__ok">
                ✓ {{ geoSelected.label || form.birth_place }}<br />
                <span class="place__coords">{{ fmtCoords(geoSelected) }}</span>
              </div>

              <div v-if="geoStatus === 'many'" class="place__many">
                <div class="place__many-label">найдено {{ geoCandidates.length }} мест — выбери:</div>
                <label
                  v-for="(c, i) in geoCandidates"
                  :key="`${c.lat}-${c.lon}`"
                  class="place__candidate"
                >
                  <input
                    type="radio"
                    :value="i"
                    v-model="geoSelectedIdx"
                  />
                  <span class="place__candidate-label">{{ c.label || form.birth_place }}</span>
                  <span class="place__candidate-coords">{{ fmtCoords(c) }}</span>
                </label>
              </div>

              <div v-if="geoStatus === 'not_found'" class="place__error">
                место не найдено — проверь написание или сотри поле, если место неизвестно
              </div>

              <div v-if="geoStatus === 'error'" class="place__error">
                геокодер недоступен — можно сохранить без координат (асцендент тогда не посчитается)
              </div>
            </div>
          </div>

          <div class="row">
            <div class="field">
              <div class="v-field-label">Пол</div>
              <select v-model="form.gender" class="v-select">
                <option :value="null">—</option>
                <option v-for="g in genders" :key="g.value" :value="g.value">{{ g.label }}</option>
              </select>
            </div>
            <div class="field">
              <div class="v-field-label">Взгляд</div>
              <select v-model="form.eye_color" class="v-select">
                <option :value="null">—</option>
                <option v-for="c in eyeColors" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
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
            <NuxtLink to="/" class="v-btn--link">← к реестру</NuxtLink>
            <button type="submit" class="v-btn" :disabled="submitting">
              {{ submitting ? 'сводим…' : '✦ свести источники ✦' }}
            </button>
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

.form { margin-top: 8px; }

.row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  margin-bottom: 18px;
}
.row:has(> .field:nth-child(2):last-child) { grid-template-columns: 1fr 1fr; }

.field { display: flex; flex-direction: column; }
.required { color: var(--terra); }

.garden { margin-top: 8px; }
.garden__row { grid-template-columns: 1fr 1fr; margin-bottom: 14px; }
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
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid var(--rule);
}

@media (max-width: 640px) {
  .row, .garden__row { grid-template-columns: 1fr; gap: 14px; }
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
.place__ok {
  margin-top: 6px;
  padding: 8px 10px;
  background: var(--paper-deep);
  border-left: 2px solid var(--leaf);
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
  line-height: 1.4;
}
.place__coords {
  font-family: var(--sans);
  font-size: 13px;
  color: var(--ink-faded);
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
  margin-top: 6px;
  padding: 8px 10px;
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
  margin-bottom: 6px;
}
.place__candidate {
  display: grid;
  grid-template-columns: 18px 1fr auto;
  gap: 8px;
  align-items: baseline;
  padding: 4px 0;
  border-bottom: 1px dotted var(--rule);
  cursor: pointer;
}
.place__candidate:last-child { border-bottom: none; }
.place__candidate-label {
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
}
.place__candidate-coords {
  font-family: var(--sans);
  font-size: 11px;
  color: var(--ink-faded);
  white-space: nowrap;
}
</style>
