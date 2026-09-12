// test/copy-denylist.test.ts
//
// Student-facing copy must describe the work, never the student, and must
// never read as a sales pitch. Mirrors cde/features.py's DENYLIST.
import { describe, it, expect } from 'vitest';

const DENYLIST = /\b(careless|unmotivated|lazy|weak student|poor grasp|anxious|stressed|struggling emotionally|panic|streaks?|badges?|points|trophy|trophies|days[ _]?active|upgrade|premium|prices?|pricing|leaderboard|percentiles?)\b/i;

function stripToCopy(src: string): string {
  // Keep this a copy scanner, not a code scanner: strip comments, import
  // lines, and JSX/HTML tag markup (so component names like <Badge> and
  // prop names don't collide with denylisted words in real user-facing text).
  return src
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/.*$/gm, '')
    .replace(/^\s*import .*$/gm, '')
    .replace(/<\/?[A-Za-z][^>]*>/g, ' ');
}

describe('student-facing copy contains no denylisted terms', () => {
  const modules = import.meta.glob('../features/student/**/*.{ts,tsx}', {
    query: '?raw',
    import: 'default',
    eager: true,
  }) as Record<string, string>;

  const files = Object.entries(modules).filter(([path]) => !path.endsWith('.test.tsx'));

  it('found student feature files to scan', () => {
    expect(files.length).toBeGreaterThan(0);
  });

  for (const [path, raw] of files) {
    it(`${path} has no denylisted copy`, () => {
      const stripped = stripToCopy(raw);
      const lines = stripped.split('\n');
      const hits: string[] = [];
      lines.forEach((line, i) => {
        const match = line.match(DENYLIST);
        if (match) hits.push(`${path}:${i + 1}: ${match[0]}`);
      });
      expect(hits).toEqual([]);
    });
  }
});
