/**
 * Тонкая обёртка над $fetch. Дальше можно расширять (auth, ошибки, etc).
 *
 * SSR (внутри docker-сети) ходит на http://api:8000 через config.apiBaseServer,
 * браузер — на http://localhost:8100 через config.public.apiBase.
 */
export const useApi = () => {
  const config = useRuntimeConfig()
  const base = import.meta.server ? (config.apiBaseServer as string) : config.public.apiBase

  return {
    get: <T = any>(path: string) => $fetch<T>(`${base}${path}`),
    post: <T = any>(path: string, body: any) =>
      $fetch<T>(`${base}${path}`, { method: 'POST', body }),
    patch: <T = any>(path: string, body: any) =>
      $fetch<T>(`${base}${path}`, { method: 'PATCH', body }),
    del: <T = any>(path: string) =>
      $fetch<T>(`${base}${path}`, { method: 'DELETE' }),
  }
}
