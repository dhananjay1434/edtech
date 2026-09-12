import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readTheme, applyTheme } from './theme';

function mockMatchMedia(matches: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })) as unknown as typeof window.matchMedia;
}

describe('theme', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('defaults to system when nothing is stored', () => {
    expect(readTheme()).toBe('system');
  });

  it('system follows matchMedia dark preference', () => {
    mockMatchMedia(true);
    applyTheme('system');
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    mockMatchMedia(false);
    applyTheme('system');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('an explicit choice persists and toggles the dark class regardless of system preference', () => {
    mockMatchMedia(false);
    applyTheme('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    window.localStorage.setItem('cde.theme', 'dark');
    expect(readTheme()).toBe('dark');
  });
});
