<script setup lang="ts">
import type { Person } from '~/composables/useApi'

const api = useApi()
const { data: persons, refresh, error } = await useAsyncData<Person[]>('persons', () => api.listPersons())

const fmtDate = (d: string) => d
const fullName = (p: Person) =>
  [p.last_name, p.first_name, p.middle_name].filter(Boolean).join(' ') || p.first_name

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

        <ul v-else class="persons">
          <li v-for="p in persons" :key="p.id" class="persons__row">
            <div class="persons__main">
              <div class="persons__name">{{ fullName(p) }}</div>
              <div class="persons__meta">
                {{ fmtDate(p.birth_date) }}
                <template v-if="p.birth_place"> · {{ p.birth_place }}</template>
                <template v-if="p.eye_color"> · взгляд {{ p.eye_color }}</template>
                <template v-if="p.garden_zone_usda"> · зона {{ p.garden_zone_usda }}</template>
              </div>
            </div>
            <div class="persons__actions">
              <NuxtLink :to="`/expert/${p.id}`" class="v-btn">пул растений →</NuxtLink>
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
.persons__name {
  font-family: var(--display);
  font-size: 22px;
  color: var(--ink);
}
.persons__meta {
  font-family: var(--serif);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-faded);
  margin-top: 4px;
}

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
