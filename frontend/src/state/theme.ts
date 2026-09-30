import { useEffect, useState } from 'react'

export type Theme = 'dark' | 'light'
const KEY = 'crisis-command-theme'

function stored(): Theme | null {
  try {
    const value = window.localStorage.getItem(KEY)
    return value === 'dark' || value === 'light' ? value : null
  } catch {
    return null
  }
}

/** Dark "operations" theme by default; the operator's choice persists per browser. */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => stored() ?? 'dark')
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      window.localStorage.setItem(KEY, theme)
    } catch {
      // Private mode or blocked storage: the theme still applies for this session.
    }
  }, [theme])
  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))]
}
