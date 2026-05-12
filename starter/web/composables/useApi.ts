/**
 * Тонкая обёртка над $fetch к FastAPI-бэку.
 *
 * SSR (внутри docker-сети) ходит на http://api:8000 через config.apiBaseServer,
 * браузер — на http://localhost:8100 через config.public.apiBase.
 */

export type Gender = 'female' | 'male' | 'other'
export type EyeColor = 'blue' | 'grey' | 'green' | 'hazel' | 'brown' | 'dark' | 'amber'
export type GardenSoil = 'dry' | 'normal' | 'wet'
export type GardenSun = 'sun' | 'part_shade' | 'shade' | 'mixed'

export interface PersonInput {
  first_name: string
  middle_name?: string | null
  last_name?: string | null
  gender?: Gender | null

  birth_date: string         // YYYY-MM-DD
  birth_time?: string | null // HH:MM
  birth_place?: string | null
  birth_lat?: number | null
  birth_lon?: number | null
  birth_tz?: string | null

  eye_color?: EyeColor | null

  garden_zone_usda?: number | null
  garden_region?: string | null
  garden_soil?: GardenSoil | null
  garden_sun?: GardenSun | null
  garden_size_m2?: number | null
  garden_style?: string | null

  notes?: string | null
}

export type PersonStatus = 'intake' | 'pool' | 'leaf'

export interface Person extends PersonInput {
  id: number
  created_at: string
  updated_at: string
  // Деривативные поля от бэка для UI реестра (см. routes/persons.py list_persons).
  status?: PersonStatus | null
  last_touch_at?: string | null
  has_share_token?: boolean
}

export interface OracleSource {
  oracle_id: string
  oracle_name: string
  weight: number
  role?: string | null
  reason_for_expert: string
  reason_for_client: string
}

export interface PoolEntry {
  plant_slug: string
  plant_name_ru?: string | null
  plant_short_story?: string | null
  match_count: number
  total_weight: number
  sources: OracleSource[]
  notes: string[]
}

export interface Exclusion {
  plant_slug: string
  reason: string
}

export interface RecommendOutput {
  active_oracles: string[]
  pool: PoolEntry[]
  filters_applied: boolean
  excluded: Exclusion[]
}

export interface OracleInfo {
  id: string
  name: string
  description?: string | null
  weight: number
  active: boolean
  implemented: boolean
}

export interface CuratedItem {
  plant_slug: string
  expert_note?: string | null
}

export interface CuratedSave {
  // новое API: per-plant заметки эксперта (D9)
  curated: CuratedItem[]
  title_plant_slug: string | null
  expert_notes?: string | null  // общая заметка на весь подбор — остаётся
  apply_filters?: boolean
}

export interface RecommendationOut {
  id: number
  person_id: number
  input_snapshot: Record<string, any>
  active_oracles: string[]
  raw_pool: PoolEntry[]
  curated_pool: CuratedItem[] | null
  title_plant_slug: string | null
  expert_notes: string | null
  share_token: string | null
  is_final: boolean
  created_at: string
  updated_at: string
}

export interface GeocodeCandidate {
  lat: number
  lon: number
  tz: string | null
  label: string | null
}

export interface RecommendationSummary {
  id: number
  person_id: number
  title_plant_slug: string | null
  curated_pool: CuratedItem[] | null
  expert_notes: string | null
  is_final: boolean
  created_at: string
  updated_at: string
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const base = import.meta.server ? (config.apiBaseServer as string) : config.public.apiBase

  const url = (path: string) => `${base}${path}`

  return {
    // raw
    get:   <T = any>(path: string) => $fetch<T>(url(path)),
    post:  <T = any>(path: string, body: any) => $fetch<T>(url(path), { method: 'POST', body }),
    patch: <T = any>(path: string, body: any) => $fetch<T>(url(path), { method: 'PATCH', body }),
    del:   <T = any>(path: string) => $fetch<T>(url(path), { method: 'DELETE' }),

    // persons
    listPersons:  () => $fetch<Person[]>(url('/persons/')),
    getPerson:    (id: number) => $fetch<Person>(url(`/persons/${id}`)),
    createPerson: (payload: PersonInput) => $fetch<Person>(url('/persons/'), { method: 'POST', body: payload }),
    deletePerson: (id: number) => $fetch(url(`/persons/${id}`), { method: 'DELETE' }),

    // recommend
    recommend: (personId: number, applyFilters = true, disabledOracles: string[] = []) => {
      const q = new URLSearchParams({ apply_filters: String(applyFilters) })
      if (disabledOracles.length) q.set('disabled', disabledOracles.join(','))
      return $fetch<RecommendOutput>(url(`/recommend/?${q}`), {
        method: 'POST',
        body: { person_id: personId },
      })
    },

    // oracles
    listOracles: () => $fetch<OracleInfo[]>(url('/oracles/')),

    // curated (этап 8)
    saveCurated: (personId: number, payload: CuratedSave) =>
      $fetch<RecommendationOut>(url(`/persons/${personId}/recommendation`), {
        method: 'PUT',
        body: payload,
      }),
    getCurated: (personId: number) =>
      $fetch<RecommendationOut>(url(`/persons/${personId}/recommendation`)),

    // история версий рекомендаций (D8)
    listRecommendations: (personId: number) =>
      $fetch<RecommendationSummary[]>(url(`/persons/${personId}/recommendations`)),
    getRecommendationVersion: (personId: number, recId: number) =>
      $fetch<RecommendationOut>(url(`/persons/${personId}/recommendations/${recId}`)),

    // публичный лист по shareable-токену (A8)
    getLeaf: (token: string) =>
      $fetch<RecommendationOut>(url(`/leaf/${token}`)),

    // пометить версию подбора финальной (E3) — снимает флаг с предыдущих
    finalizeRecommendation: (personId: number, recId: number) =>
      $fetch<RecommendationOut>(url(`/persons/${personId}/recommendations/${recId}/finalize`), {
        method: 'POST',
      }),

    // геокодинг места рождения (F1)
    searchPlaces: (q: string, limit = 5) =>
      $fetch<GeocodeCandidate[]>(url(`/geocode/?q=${encodeURIComponent(q)}&limit=${limit}`)),

    // PDF — собираем url, чтобы фронт открывал в новой вкладке (нет смысла тащить blob).
    // Всегда берём public base (даже при SSR-вызове), потому что href будет кликаться в браузере,
    // а http://api:8000 из docker-сети недоступен снаружи.
    reportPdfUrl: (personId: number) => `${config.public.apiBase}/reports/${personId}.pdf`,
  }
}
