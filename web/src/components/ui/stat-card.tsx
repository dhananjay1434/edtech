// components/ui/stat-card.tsx
//
// "No card shows only a number with no explanation" — context and action are
// required props, not optional, so the type system enforces it.
import { Link } from 'react-router-dom';
import { cn } from 'cn';

export type StatValue = string | { notRecorded: true };
export type StatAction = { label: string; to: string } | { label: string; onClick: () => void };
export type StatTone = 'neutral' | 'success' | 'attention';

const TONE_CLASS: Record<StatTone, string> = {
  neutral: 'text-foreground',
  success: 'text-success',
  attention: 'text-attention',
};

export function StatCard({ label, value, context, action, tone = 'neutral', className }: {
  label: string;
  value: StatValue;
  context: string;
  action: StatAction;
  tone?: StatTone;
  className?: string;
}) {
  const display = typeof value === 'string' ? value : 'Not recorded';
  const isRecorded = typeof value === 'string';

  return (
    <div className={cn('rounded-lg border border-border p-4', className)} data-testid="stat-card">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className={cn('mt-1 text-2xl font-semibold tabular-nums',
        isRecorded ? TONE_CLASS[tone] : 'text-muted-foreground text-base font-medium')}>
        {display}
      </p>
      <p className="mt-1 text-xs text-muted-foreground" data-testid="stat-card-context">{context}</p>
      {'to' in action ? (
        <Link to={action.to} className="mt-2 inline-block text-sm font-medium text-primary hover:underline"
          data-testid="stat-card-action">
          {action.label}
        </Link>
      ) : (
        <button type="button" onClick={action.onClick}
          className="mt-2 text-sm font-medium text-primary hover:underline" data-testid="stat-card-action">
          {action.label}
        </button>
      )}
    </div>
  );
}
