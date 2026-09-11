// shared/Evidence.tsx
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRuntime } from '../app/providers';
import type { Portal } from '../api/contracts';

export function Evidence({ cropId, audience, onReady }: {
  cropId: string;
  audience: Portal;
  onReady?: (ready: boolean) => void;
}) {
  const { api, scope } = useRuntime();
  const [src, setSrc] = useState('');
  const [broken, setBroken] = useState(false);
  const query = useQuery({
    queryKey: [scope, 'evidence', audience, cropId],
    queryFn: ({ signal }) => api.cropBlob(audience, cropId, signal),
    gcTime: 0,
    staleTime: Infinity
  });

  useEffect(() => {
    onReady?.(false);
    if (!query.data) return;
    const url = URL.createObjectURL(query.data);
    setSrc(url);
    setBroken(false);
    return () => {
      URL.revokeObjectURL(url);
      onReady?.(false);
    };
  }, [query.data, onReady]);

  if (query.isError || broken) return (
    <div role="alert">
      <p>Evidence is unavailable. Do not resolve this answer without it.</p>
      <button onClick={() => void query.refetch()}>Reload evidence</button>
    </div>
  );
  if (!src) return <div role="status" className="h-56 animate-pulse bg-slate-100">Loading evidence…</div>;

  return <img src={src} alt="Scanned handwritten answer"
    className="max-h-[65vh] w-full rounded-lg border border-slate-200 object-contain"
    referrerPolicy="no-referrer"
    onLoad={() => onReady?.(true)}
    onError={() => { setBroken(true); onReady?.(false); }} />;
}
