// features/student/FeatureGate.tsx
//
// Renders the real feature when the institute has enabled it, otherwise an
// honest locked card: what the feature does, that it isn't enabled yet, and
// a clearly-labelled sample so a student can see what it would look like.
// No price, no "upgrade", no date — those are never shown on this surface.
import type { ReactNode } from 'react';
import { useFeature } from './useFeatures';
import type { FeatureEntry, FeatureKey } from '../../api/student';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';

export function LockedFeature({ entry, sample }: { entry: FeatureEntry; sample: ReactNode }) {
  return (
    <Card data-testid={`locked-feature-${entry.key}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>{entry.title}</CardTitle>
          <Badge variant="secondary">{entry.status === 'available' ? 'Available' : 'Preview'}</Badge>
        </div>
        <CardDescription>{entry.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground" data-testid="locked-notice">
          Not enabled for your institute yet.
        </p>
        <section aria-label="Example" data-testid="sample-preview" className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">
            Example — not your data (fictional student: Asha R.)
          </p>
          {sample}
        </section>
      </CardContent>
    </Card>
  );
}

export function FeatureGate({ feature, sample, children }: {
  feature: FeatureKey;
  sample: ReactNode;
  children: ReactNode;
}) {
  const { enabled, entry, isPending, isError } = useFeature(feature);

  if (isPending) return <Skeleton className="h-40 w-full" data-testid="feature-gate-loading" />;

  if (isError || !entry) {
    return (
      <Alert variant="destructive" data-testid="feature-gate-error">
        <AlertTitle>Could not check what's available</AlertTitle>
        <AlertDescription>Please try again in a moment.</AlertDescription>
      </Alert>
    );
  }

  if (!enabled) return <LockedFeature entry={entry} sample={sample} />;

  return <>{children}</>;
}
