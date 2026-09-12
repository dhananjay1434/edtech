// features/student/useFeatures.ts
import { useQuery } from '@tanstack/react-query';
import { listFeatures, type FeatureEntry, type FeatureKey } from '../../api/student';

export function useFeatures() {
  return useQuery({
    queryKey: ['student', 'features'],
    queryFn: async () => (await listFeatures()).features,
    staleTime: 60_000,
  });
}

export function useFeature(key: FeatureKey): {
  enabled: boolean;
  entry: FeatureEntry | undefined;
  isPending: boolean;
  isError: boolean;
} {
  const query = useFeatures();
  const entry = query.data?.find(f => f.key === key);
  return {
    enabled: entry?.enabled ?? false,
    entry,
    isPending: query.isPending,
    isError: query.isError,
  };
}
