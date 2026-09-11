// features/admin/RosterImportPanel.tsx
//
// CSV import with a preview and per-row validation before committing —
// nothing is written to the roster until the admin confirms.
import { useMemo, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { importRoster, AdminApiError, type RosterRowInput } from '../../api/admin';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '../../components/ui/table';

interface ParsedRow {
  line: number;
  roll_number: string;
  name: string;
  errors: string[];
}

function parseCsv(text: string): ParsedRow[] {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const seen = new Map<string, number>();
  const rows: ParsedRow[] = [];
  lines.forEach((line, idx) => {
    const lineNumber = idx + 1;
    // Skip an optional header row.
    if (idx === 0 && /roll/i.test(line) && /name/i.test(line)) return;
    const [rollRaw = '', nameRaw = ''] = line.split(',').map(s => s.trim());
    const errors: string[] = [];
    if (!rollRaw) errors.push('Missing roll number');
    if (!nameRaw) errors.push('Missing name');
    const key = rollRaw.toUpperCase();
    if (rollRaw && seen.has(key)) {
      errors.push(`Duplicate of line ${seen.get(key)}`);
    } else if (rollRaw) {
      seen.set(key, lineNumber);
    }
    rows.push({ line: lineNumber, roll_number: rollRaw, name: nameRaw, errors });
  });
  return rows;
}

export function RosterImportPanel() {
  const [examClass, setExamClass] = useState('');
  const [rows, setRows] = useState<ParsedRow[]>([]);
  const [fileName, setFileName] = useState('');
  const [result, setResult] = useState<{ roster_id: string; student_count: number } | null>(null);
  const input = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: (payload: { exam_class: string; rows: RosterRowInput[] }) =>
      importRoster(payload.exam_class, payload.rows),
  });

  const validRows = useMemo(() => rows.filter(r => r.errors.length === 0), [rows]);
  const hasErrors = rows.some(r => r.errors.length > 0);
  const canCommit = examClass.trim().length > 0 && rows.length > 0 && !hasErrors;

  async function onFile(file: File | undefined) {
    if (!file) return;
    setFileName(file.name);
    setResult(null);
    const text = await file.text();
    setRows(parseCsv(text));
  }

  async function commit() {
    if (!canCommit) return;
    setResult(null);
    const created = await mutation.mutateAsync({
      exam_class: examClass.trim(),
      rows: validRows.map(r => ({ roll_number: r.roll_number, name: r.name })),
    });
    setResult(created);
    setRows([]);
    setFileName('');
    if (input.current) input.current.value = '';
  }

  return (
    <Card data-testid="roster-import-panel">
      <CardHeader>
        <CardTitle>Import roster</CardTitle>
        <CardDescription>
          CSV with two columns: roll number, name. Nothing is saved until you confirm below.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="exam-class">Class</Label>
          <Input id="exam-class" placeholder="e.g. 12A" value={examClass}
            onChange={e => setExamClass(e.target.value)} data-testid="exam-class-input" />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="roster-csv">CSV file</Label>
          <input ref={input} id="roster-csv" type="file" accept=".csv,text/csv"
            data-testid="roster-csv-input"
            onChange={e => void onFile(e.target.files?.[0])} />
          {fileName && <p className="text-sm text-muted-foreground">{fileName} — {rows.length} row(s) found</p>}
        </div>

        {rows.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="font-medium">Preview</h3>
              <Badge variant={hasErrors ? 'destructive' : 'default'} data-testid="roster-preview-status">
                {hasErrors ? `${rows.length - validRows.length} row(s) need fixing` : 'All rows valid'}
              </Badge>
            </div>
            <div className="max-h-80 overflow-y-auto rounded-lg border border-border">
              <Table data-testid="roster-preview-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Line</TableHead>
                    <TableHead>Roll number</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map(r => (
                    <TableRow key={r.line} data-testid={`roster-row-${r.line}`}>
                      <TableCell>{r.line}</TableCell>
                      <TableCell>{r.roll_number || <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell>{r.name || <span className="text-muted-foreground">—</span>}</TableCell>
                      <TableCell>
                        {r.errors.length === 0
                          ? <Badge>OK</Badge>
                          : <Badge variant="destructive" title={r.errors.join('; ')}>{r.errors[0]}</Badge>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {mutation.isError && (
          <Alert variant="destructive">
            <AlertTitle>Import failed</AlertTitle>
            <AlertDescription>
              {mutation.error instanceof AdminApiError ? mutation.error.detail : 'Please try again.'}
            </AlertDescription>
          </Alert>
        )}

        {result && (
          <Alert data-testid="roster-import-success">
            <AlertTitle>Roster imported</AlertTitle>
            <AlertDescription>
              {result.student_count} students added to roster {result.roster_id}.
            </AlertDescription>
          </Alert>
        )}

        <button className="action" data-testid="roster-commit-button"
          disabled={!canCommit || mutation.isPending} onClick={() => void commit()}>
          {mutation.isPending ? 'Importing…' : `Import ${validRows.length || ''} students`}
        </button>
      </CardContent>
    </Card>
  );
}
