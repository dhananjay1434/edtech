// features/admin/FeaturesPanel.tsx
//
// Lets the institute admin turn student-facing preview features on or off.
// One entitlements document backs every student's GET /api/me/features.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getFeatures, putFeatures } from '../../api/admin';
import type { FeatureKey } from '../../api/student';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';

export function FeaturesPanel() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['admin', 'features'], queryFn: getFeatures });

  const mutation = useMutation({
    mutationFn: (patch: Partial<Record<FeatureKey, boolean>>) => putFeatures(patch),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['admin', 'features'] }),
  });

  return (
    <Card data-testid="features-panel">
      <CardHeader>
        <CardTitle>Student features</CardTitle>
        <CardDescription>
          Turn on the features your institute is ready to offer students. Everything else
          still shows students what it is, marked as not enabled yet.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {query.isPending && <Skeleton className="h-64 w-full" />}
        {query.isSuccess && query.data.features.map(f => (
          <div key={f.key} className="flex items-center justify-between gap-4 rounded-lg border border-border p-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium">{f.title}</span>
                <Badge variant="secondary">{f.status === 'available' ? 'Available' : 'Preview'}</Badge>
              </div>
              <p className="text-sm text-muted-foreground">{f.description}</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={f.enabled}
              aria-label={f.title}
              data-testid={`feature-switch-${f.key}`}
              onClick={() => mutation.mutate({ [f.key]: !f.enabled })}
              disabled={mutation.isPending}
              className={`h-6 w-11 shrink-0 rounded-full border border-input transition-colors ${
                f.enabled ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span className={`block h-4 w-4 rounded-full bg-background transition-transform ${
                f.enabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
