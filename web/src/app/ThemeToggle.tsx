// app/ThemeToggle.tsx
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme, type Theme } from './theme';

const OPTIONS: Array<{ value: Theme; label: string; Icon: typeof Sun }> = [
  { value: 'light', label: 'Light', Icon: Sun },
  { value: 'dark', label: 'Dark', Icon: Moon },
  { value: 'system', label: 'System', Icon: Monitor },
];

export function ThemeToggle() {
  const [theme, setTheme] = useTheme();

  return (
    <div role="radiogroup" aria-label="Theme" className="flex gap-1 rounded-lg border border-border p-1">
      {OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={theme === value}
          aria-label={label}
          data-testid={`theme-${value}`}
          onClick={() => setTheme(value)}
          className={`flex h-9 w-9 items-center justify-center rounded-md transition-colors ${
            theme === value ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Icon className="h-4 w-4" aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}
