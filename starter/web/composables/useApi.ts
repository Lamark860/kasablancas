/**
 * Тонкая обёртка над $fetch. Дальше можно расширять (auth, ошибки, etc).
 */
export const useApi = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase
  
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
