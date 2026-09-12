// app/theme.ts — light/dark/system theme, persisted, wiring the .dark
// token block in styles.css that nothing previously toggled.
import { useCallback, useEffect, useState } from 'react';

export type Theme = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'cde.theme';

function prefersDark(): boolean {
  return typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-color-scheme: dark)').matches === true;
}

export function readTheme(): Theme {
  if (typeof window === 'undefined') return 'system';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system';
}

export function applyTheme(theme: Theme): void {
  const dark = theme === 'dark' || (theme === 'system' && prefersDark());
  const root = document.documentElement;
  root.classList.toggle('dark', dark);
  root.style.colorScheme = dark ? 'dark' : 'light';
}

export function useTheme(): [Theme, (theme: Theme) => void] {
  const [theme, setThemeState] = useState<Theme>(readTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (theme !== 'system') return;
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => applyTheme('system');
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    window.localStorage.setItem(STORAGE_KEY, next);
    setThemeState(next);
  }, []);

  return [theme, setTheme];
}
