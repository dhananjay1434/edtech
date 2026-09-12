// test/render.tsx — shared test harness for student/admin components.
import type { ReactNode } from 'react';
import { render, type RenderResult } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi } from 'vitest';
import { Providers } from '../app/providers';
import type { CdeApi, Portal, Runtime } from '../api/contracts';
import type { FeatureEntry, FeatureKey } from '../api/student';

export function makeRuntime(overrides: Partial<CdeApi> = {}, portals: Portal[] = ['student']): Runtime {
  const api: CdeApi = {
    accessToken: async () => 'token',
    prepareUpload: vi.fn(),
    completeUpload: vi.fn(),
    submissionStatus: vi.fn(),
    reviewQueue: vi.fn(),
    resolveTask: vi.fn(),
    studentExam: vi.fn(),
    myExamReport: vi.fn(),
    cropBlob: vi.fn(),
    ...overrides,
  };
  return { api, scope: 'test', portals, signOut: async () => {} };
}

export function renderStudent(ui: ReactNode, opts: {
  route?: string;
  path?: string;
  runtime?: Runtime;
} = {}): RenderResult {
  const { route = '/', path = '*', runtime = makeRuntime() } = opts;
  return render(
    <Providers runtime={runtime}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={ui} />
        </Routes>
      </MemoryRouter>
    </Providers>,
  );
}

// One catalog entry per key, all disabled by default — mirrors cde/features.py
// closely enough for component tests, without importing Python.
const ALL_KEYS: FeatureKey[] = [
  'cognitive.diagnosis', 'cognitive.growth', 'cognitive.heatmap',
  'cognitive.patterns', 'cognitive.calibration', 'cognitive.exam_history',
  'learning.spaced_review', 'learning.planner', 'learning.micro_wins', 'learning.trajectory',
];

const TIER: Record<FeatureKey, 2 | 3> = {
  'cognitive.diagnosis': 2, 'cognitive.growth': 2, 'cognitive.heatmap': 2,
  'cognitive.patterns': 2, 'cognitive.calibration': 2, 'cognitive.exam_history': 2,
  'learning.spaced_review': 3, 'learning.planner': 3, 'learning.micro_wins': 3, 'learning.trajectory': 3,
};

const STATUS: Record<FeatureKey, 'available' | 'preview'> = {
  'cognitive.diagnosis': 'available', 'cognitive.growth': 'available', 'cognitive.heatmap': 'available',
  'cognitive.patterns': 'preview', 'cognitive.calibration': 'preview', 'cognitive.exam_history': 'preview',
  'learning.spaced_review': 'preview', 'learning.planner': 'preview',
  'learning.micro_wins': 'preview', 'learning.trajectory': 'preview',
};

export const SAMPLE_FEATURES: FeatureEntry[] = ALL_KEYS.map(key => ({
  key,
  title: key,
  description: `Description for ${key}`,
  tier: TIER[key],
  status: STATUS[key],
  enabled: false,
}));

export function featuresWith(enabledKeys: FeatureKey[]): { features: FeatureEntry[] } {
  return {
    features: SAMPLE_FEATURES.map(f => ({ ...f, enabled: enabledKeys.includes(f.key) })),
  };
}
