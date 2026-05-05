<script setup lang="ts">
const api = useApi()
const { data: ping } = await useAsyncData('ping', () => api.get('/ping'))
</script>

<template>
  <main class="page">
    <h1>Vlad rev1</h1>
    <p>Hello world. API: <code>{{ ping }}</code></p>
    <p>Дальше — наполнять по <code>handoff/04-roadmap.md</code>.</p>
  </main>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 80px auto;
  padding: 0 24px;
  font-family: 'Cormorant Garamond', Georgia, serif;
}
h1 { font-size: 48px; margin-bottom: 24px; }
code { background: #f3efe6; padding: 2px 6px; border-radius: 3px; }
</style>
