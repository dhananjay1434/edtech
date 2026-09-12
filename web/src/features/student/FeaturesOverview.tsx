// features/student/FeaturesOverview.tsx
//
// "What your institute can enable" — every catalog feature, honestly
// labelled. No purchase call to action anywhere on this page.
import { Link } from 'react-router-dom';
import { useFeatures } from './useFeatures';
import type { FeatureEntry } from '../../api/student';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';

const ROUTE_BY_KEY: Record<string, string> = {
  'cognitive.diagnosis': '/student/exams',
  'cognitive.growth': '/student/growth',
  'cognitive.heatmap': '/student/growth/topics',
  'cognitive.patterns': '/student/growth/patterns',
  'cognitive.calibration': '/student/growth/calibration',
  'cognitive.exam_history': '/student/growth/history',
  'learning.spaced_review': '/student/practice',
  'learning.planner': '/student/plan',
  'learning.micro_wins': '/student/growth',
  'learning.trajectory': '/student/growth/insight',
};

function FeatureRow({ feature }: { feature: FeatureEntry }) {
  const to = ROUTE_BY_KEY[feature.key];
  return (
    <div data-testid={`feature-overview-${feature.key}`}
      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border p-3">
      <div>
        <div className="flex items-center gap-2">
          <span className="font-medium">{feature.title}</span>
          <Badge variant="outline">{feature.tier === 2 ? 'Insight' : 'Learning'}</Badge>
          <Badge variant="secondary">{feature.status === 'available' ? 'Available now' : 'Preview'}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{feature.description}</p>
        <p className="text-sm text-muted-foreground">
          {feature.enabled ? 'Enabled for you' : 'Not enabled for your institute yet'}
        </p>
      </div>
      {to && (
        <Link to={to} className="text-sm font-medium text-primary hover:underline">
          Open
        </Link>
      )}
    </div>
  );
}

export function FeaturesOverview() {
  const query = useFeatures();

  return (
    <Card data-testid="features-overview">
      <CardHeader>
        <CardTitle>What your institute can enable</CardTitle>
        <CardDescription>
          These are the features built into this portal. Your institute decides which are on.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {query.isPending && <Skeleton className="h-64 w-full" />}
        {query.isError && (
          <Alert variant="destructive">
            <AlertTitle>Could not load features</AlertTitle>
            <AlertDescription>Please try again in a moment.</AlertDescription>
          </Alert>
        )}
        {query.isSuccess && query.data.map(f => <FeatureRow key={f.key} feature={f} />)}
      </CardContent>
    </Card>
  );
}
