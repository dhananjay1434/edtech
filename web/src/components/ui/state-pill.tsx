// components/ui/state-pill.tsx
//
// State is never communicated by colour alone — icon and text both change.
// "Not correct yet" (muted terra-cotta), never "Wrong" (saturated red).
import { Check, Minus, Circle, CircleDot, Eye } from 'lucide-react';
import { cn } from 'cn';
import type { AwardState } from '../../api/contracts';

const CONFIG: Record<AwardState, { label: string; Icon: typeof Check; className: string }> = {
  correct: { label: 'Correct', Icon: Check, className: 'text-success' },
  incorrect: { label: 'Not correct yet', Icon: Minus, className: 'text-attention' },
  blank: { label: 'Left blank', Icon: Circle, className: 'text-muted-foreground' },
  invalid_multiple: { label: 'More than one bubble', Icon: CircleDot, className: 'text-attention' },
  pending_review: { label: 'Being checked by a person', Icon: Eye, className: 'text-muted-foreground' },
};

export function StatePill({ state, className }: { state: AwardState; className?: string }) {
  const { label, Icon, className: toneClass } = CONFIG[state];
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-sm font-medium', toneClass, className)}
      data-testid="state-pill">
      <Icon className="h-4 w-4" aria-hidden="true" />
      {label}
    </span>
  );
}
