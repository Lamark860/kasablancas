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
  
  css: ['~/assets/styles/globals.css'],
  
  app: {
    head: {
      title: 'Vlad rev1',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      ],
    },
  },
})
