// app/providers.tsx
import { createContext, useContext, useState, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { Runtime } from '../api/contracts';
import { retryRead } from '../api/contracts';

const RuntimeContext = createContext<Runtime | null>(null);

export function useRuntime(): Runtime {
  const value = useContext(RuntimeContext);
  if (!value) throw new Error('Runtime provider missing');
  return value;
}

export function Providers({ runtime, children }: {
  runtime: Runtime;
  children: ReactNode;
}) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 5000, retry: retryRead },
      mutations: { retry: false }
    }
  }));

  return (
    <RuntimeContext.Provider value={runtime}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </RuntimeContext.Provider>
  );
}
