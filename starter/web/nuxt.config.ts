// nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },

  runtimeConfig: {
    apiBaseServer: process.env.NUXT_API_BASE_SERVER || 'http://api:8000',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8100',
    },
  },

  css: [
    '~/assets/styles/globals.css',
    '~/assets/styles/victorian.css',
  ],

  app: {
    head: {
      title: 'Hortus Animæ — Vlad rev1',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=UnifrakturCook:wght@700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap',
        },
      ],
    },
  },
})
