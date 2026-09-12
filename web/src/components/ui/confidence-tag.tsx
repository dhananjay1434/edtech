// components/ui/confidence-tag.tsx
//
// Every AI-derived value renders with its confidence and human-review state —
// never presented as ground truth. Low confidence is visually distinguished,
// not just labelled, so it can't be skimmed past.
import { cn } from 'cn';

const HIGH_CONFIDENCE = 0.9;

export function ConfidenceTag({ value, reviewed, className }: {
  value: number | null;
  reviewed: boolean;
  className?: string;
}) {
  const confidenceLabel = value === null
    ? 'No classification'
    : value >= HIGH_CONFIDENCE ? 'High confidence' : 'Low confidence';
  const lowConfidence = value !== null && value < HIGH_CONFIDENCE;

  return (
    <span className={cn('inline-flex flex-wrap items-center gap-2 text-xs', className)} data-testid="confidence-tag">
      <span className={cn('rounded-full border px-2 py-0.5 font-medium',
        lowConfidence ? 'border-dashed border-muted-foreground text-muted-foreground' : 'border-border text-foreground')}>
        {confidenceLabel}
      </span>
      <span className="text-muted-foreground">
        {reviewed ? 'Reviewed by a teacher' : 'Not yet reviewed by a teacher'}
      </span>
    </span>
  );
}
