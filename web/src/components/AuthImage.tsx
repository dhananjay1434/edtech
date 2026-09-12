// components/AuthImage.tsx
//
// A plain <img src="/api/images/..."> never sends an Authorization header —
// browsers don't attach custom headers to image requests. Since that
// endpoint now requires a bearer token (admin, or a student viewing their
// own sheet), we fetch the bytes ourselves via authFetch and hand the
// <img> a blob: URL instead.
import { useEffect, useState } from 'react';
import { authFetch } from '../auth';

export function AuthImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let url: string | null = null;
    let cancelled = false;
    setBlobUrl(null);
    setFailed(false);

    authFetch(src)
      .then(res => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.blob();
      })
      .then(blob => {
        if (cancelled) return;
        url = URL.createObjectURL(blob);
        setBlobUrl(url);
      })
      .catch(() => { if (!cancelled) setFailed(true); });

    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [src]);

  if (failed) {
    return <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">Could not load image</div>;
  }
  if (!blobUrl) {
    return <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">Loading…</div>;
  }
  return <img src={blobUrl} alt={alt} className={className} />;
}
