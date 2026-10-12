/**
 * useTheme — manages light/dark theme via class on <html>.
 * Default: follows prefers-color-scheme (auto).
 * Persists preference in localStorage.
 *
 * Usage:
 *   const { theme, setTheme, resolvedTheme } = useTheme()
 *   setTheme('dark' | 'light' | 'system')
 */
import { useEffect, useState, useCallback } from 'react'

export type ThemeMode = 'dark' | 'light' | 'system'
const STORAGE_KEY = 'ev-theme'

function getSystemTheme(): 'dark' | 'light' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(mode: ThemeMode) {
  const resolved = mode === 'system' ? getSystemTheme() : mode
  const html = document.documentElement
  if (resolved === 'dark') {
    html.classList.remove('light')
    html.classList.add('dark')
  } else {
    html.classList.remove('dark')
    html.classList.add('light')
  }
  return resolved
}

export function useTheme() {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    try {
      return (localStorage.getItem(STORAGE_KEY) as ThemeMode) ?? 'system'
    } catch {
      return 'system'
    }
  })

  const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>(() =>
    applyTheme((localStorage.getItem(STORAGE_KEY) as ThemeMode) ?? 'system')
  )

  const setTheme = useCallback((mode: ThemeMode) => {
    try { localStorage.setItem(STORAGE_KEY, mode) } catch { /* */ }
    setThemeState(mode)
    setResolvedTheme(applyTheme(mode))
  }, [])

  // Listen for system preference changes when in 'system' mode
  useEffect(() => {
    if (theme !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => setResolvedTheme(applyTheme('system'))
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  return { theme, setTheme, resolvedTheme }
}
