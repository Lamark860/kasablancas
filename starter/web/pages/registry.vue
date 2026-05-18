<script setup lang="ts">
import type { Person, PersonStatus } from '~/composables/useApi'

const api = useApi()
const { data: persons, refresh, error } = await useAsyncData<Person[]>('persons', () => api.listPersons())

const fmtDate = (d: string) => d
const fullName = (p: Person) =>
  [p.last_name, p.first_name, p.middle_name].filter(Boolean).join(' ') || p.first_name

function fmtLastTouch(s?: string | null): string {
  if (!s) return ''
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return ''
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const day = 24 * 60 * 60 * 1000
  if (diffMs < day) return 'сегодня'
  if (diffMs < 2 * day) return 'вчера'
  if (diffMs < 7 * day) return `${Math.floor(diffMs / day)} дн. назад`
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })
}

const statusLabels: Record<PersonStatus, string> = {
  intake: 'анкета',
  pool: 'свод',
  leaf: 'лист',
}

// — Поиск и фильтр —
const searchQ = ref('')
const statusFilter = ref<PersonStatus | 'all'>('all')

const visible = computed<Person[]>(() => {
  if (!persons.value) return []
  const q = searchQ.value.trim().toLowerCase()
  return persons.value.filter((p) => {
    if (statusFilter.value !== 'all' && p.status !== statusFilter.value) return false
    if (q) {
      const hay = [p.first_name, p.middle_name, p.last_name, p.birth_place]
        .filter(Boolean).join(' ').toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })
})

const countsByStatus = computed<Record<PersonStatus | 'all', number>>(() => {
  const c = { all: 0, intake: 0, pool: 0, leaf: 0 } as Record<PersonStatus | 'all', number>
  for (const p of persons.value ?? []) {
    c.all += 1
    if (p.status) c[p.status] += 1
  }
  return c
})

const deletingId = ref<number | null>(null)
const deleteError = ref<string | null>(null)

async function deletePerson(p: Person) {
  if (!window.confirm(
    `Удалить гостью «${fullName(p)}»? Будут безвозвратно стёрты её рекомендации, натальная карта и все версии подбора. Действие необратимо.`
  )) return
  deletingId.value = p.id
  deleteError.value = null
  try {
    await api.deletePerson(p.id)
    await refresh()
  } catch (e: any) {
    deleteError.value = `не удалось удалить #${p.id}: ${e?.message || 'ошибка'}`
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <main class="v-page">
    <div class="v-sheet v-grain">
      <div class="v-frame">
        <header class="masthead">
          <div>
            <div class="masthead__eyebrow">folium · index hospitarum</div>
            <h1 class="masthead__title">Hortus Animæ</h1>
            <div class="masthead__sub">альманах растений · реестр гостий</div>
          </div>
          <NuxtLink to="/intake" class="v-btn">+ новая гостья</NuxtLink>
        </header>

        <hr class="v-rule v-rule--ink" />

        <section v-if="error" class="error">
          API недоступен: <code>{{ error.message }}</code>
        </section>

        <section v-else-if="persons && persons.length === 0" class="empty">
          <p class="empty__text">
            пока никого не записано.
            <br />начнём с <NuxtLink to="/intake">первой анкеты</NuxtLink>.
          </p>
        </section>

        <template v-else>
          <div class="reg-tools">
            <input
              v-model="searchQ"
              class="reg-search"
              type="search"
              placeholder="поиск по имени или месту…"
            />
            <div class="reg-chips">
              <button
                type="button"
                class="reg-chip"
                :class="{ 'reg-chip--active': statusFilter === 'all' }"
                @click="statusFilter = 'all'"
              >все <span class="reg-chip__count">{{ countsByStatus.all }}</span></button>
              <button
                type="button"
                class="reg-chip reg-chip--intake"
                :class="{ 'reg-chip--active': statusFilter === 'intake' }"
                @click="statusFilter = 'intake'"
              >анкета <span class="reg-chip__count">{{ countsByStatus.intake }}</span></button>
              <button
                type="button"
                class="reg-chip reg-chip--pool"
                :class="{ 'reg-chip--active': statusFilter === 'pool' }"
                @click="statusFilter = 'pool'"
              >свод <span class="reg-chip__count">{{ countsByStatus.pool }}</span></button>
              <button
                type="button"
                class="reg-chip reg-chip--leaf"
                :class="{ 'reg-chip--active': statusFilter === 'leaf' }"
                @click="statusFilter = 'leaf'"
              >лист <span class="reg-chip__count">{{ countsByStatus.leaf }}</span></button>
            </div>
          </div>

          <div v-if="visible.length === 0" class="empty">
            <p class="empty__text">
              никого не нашлось по этим условиям.
              <br />попробуй очистить поиск или фильтр.
            </p>
          </div>

          <ul v-else class="persons">
            <li v-for="p in visible" :key="p.id" class="persons__row">
              <div class="persons__main">
                <div class="persons__name-row">
                  <span class="persons__name">{{ fullName(p) }}</span>
                  <span
                    v-if="p.status"
                    class="persons__status"
                    :class="`persons__status--${p.status}`"
                  >{{ statusLabels[p.status] }}</span>
                </div>
                <div class="persons__meta">
                  {{ fmtDate(p.birth_date) }}
                  <template v-if="p.birth_place"> · {{ p.birth_place }}</template>
                  <template v-if="p.eye_color"> · взгляд {{ p.eye_color }}</template>
                  <template v-if="p.garden_zone_usda"> · зона {{ p.garden_zone_usda }}</template>
                  <span v-if="p.last_touch_at" class="persons__last">
                    · последнее касание <em>{{ fmtLastTouch(p.last_touch_at) }}</em>
                  </span>
                </div>
              </div>
              <div class="persons__actions">
                <NuxtLink
                  v-if="p.status === 'leaf'"
                  :to="`/client/${p.id}`"
                  class="v-btn"
                  title="смотреть собранный лист гостьи"
                >лист →</NuxtLink>
                <NuxtLink
                  :to="`/expert/${p.id}`"
                  class="v-btn--link persons__action"
                  :title="p.status === 'intake' ? 'свести оракулы и собрать пул' : 'продолжить подбор или сделать новую версию'"
                >{{ p.status === 'intake' ? 'свести →' : (p.status === 'leaf' ? 'новая версия' : 'продолжить →') }}</NuxtLink>
                <button
                  type="button"
                  class="persons__delete"
                  :disabled="deletingId === p.id"
                  :title="`удалить ${fullName(p)} вместе со всеми версиями подбора`"
                  @click="deletePerson(p)"
                >
                  {{ deletingId === p.id ? '…' : '× удалить' }}
                </button>
              </div>
            </li>
          </ul>
        </template>

        <div v-if="deleteError" class="error error--inline">{{ deleteError }}</div>

        <footer class="footer">
          <span class="footer__note">folium I · expertus · internal use</span>
          <button class="v-btn--link" type="button" @click="refresh()">↻ обновить</button>
        </footer>
      </div>
    </div>
  </main>
</template>

<style scoped>
.masthead {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
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
  font-size: 44px;
  line-height: 1;
  margin: 6px 0 4px;
  color: var(--ink);
}
.masthead__sub {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
}

.error {
  margin-top: 14px;
  padding: 14px;
  background: var(--paper-deep);
  border: 1px dashed var(--terra);
  font-family: var(--serif);
  font-style: italic;
  color: var(--terra);
}
.error code { font-family: var(--sans); font-size: 14px; }
.error--inline { margin-top: 12px; }

.persons__actions {
  display: flex;
  align-items: center;
  gap: 14px;
}
.persons__delete {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faded);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px 8px;
  white-space: nowrap;
}
.persons__delete:hover { color: var(--terra); }
.persons__delete:disabled { opacity: 0.4; cursor: wait; }

.empty {
  padding: 40px 0;
  text-align: center;
}
.empty__text {
  font-family: var(--serif);
  font-style: italic;
  font-size: 16px;
  color: var(--ink-faded);
  line-height: 1.6;
}
.empty__text a { font-style: italic; }

.persons {
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
}
.persons__row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--rule);
}
.persons__row:last-child { border-bottom: none; }
.persons__name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.persons__name {
  font-family: var(--display);
  font-size: 22px;
  color: var(--ink);
}
.persons__status {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 8px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  padding: 2px 6px;
  border: 1px solid currentColor;
  color: var(--ink-faded);
}
.persons__status--intake { color: var(--ink-faded); }
.persons__status--pool   { color: var(--gold, #b08d44); }
.persons__status--leaf   { color: var(--terra); }

.persons__meta {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  margin-top: 4px;
}
.persons__last em { color: var(--ink); font-style: italic; }
.persons__action {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faded);
  background: transparent;
  border: none;
  padding: 6px 8px;
  white-space: nowrap;
}
.persons__action:hover { color: var(--terra); }

/* — Tools (поиск + фильтр) — */
.reg-tools {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin: 14px 0 6px;
  padding-bottom: 12px;
  border-bottom: 1px dotted var(--rule);
}
.reg-search {
  flex: 1;
  min-width: 200px;
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  padding: 8px 12px;
  border: 1px solid var(--rule);
  background: var(--paper);
  color: var(--ink);
  outline: none;
}
.reg-search:focus { border-color: var(--terra); }
.reg-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.reg-chip {
  font-family: var(--sans);
  font-weight: 500;
  font-size: 9px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  padding: 5px 10px;
  background: transparent;
  border: 1px solid var(--rule);
  color: var(--ink-faded);
  cursor: pointer;
}
.reg-chip:hover { border-color: var(--ink); color: var(--ink); }
.reg-chip--active {
  background: var(--paper-deep);
  border-color: var(--ink);
  color: var(--ink);
}
.reg-chip__count {
  display: inline-block;
  margin-left: 4px;
  padding: 0 4px;
  font-size: 8px;
  color: var(--ink-faded);
}
.reg-chip--intake.reg-chip--active { border-color: var(--ink-faded); }
.reg-chip--pool.reg-chip--active { border-color: var(--gold, #b08d44); color: var(--gold, #b08d44); }
.reg-chip--leaf.reg-chip--active { border-color: var(--terra); color: var(--terra); }

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
</style>
