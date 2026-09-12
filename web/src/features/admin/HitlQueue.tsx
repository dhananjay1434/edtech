// features/admin/HitlQueue.tsx
//
// The bubble-review screen — where the admin will spend most of their time.
// Keyboard-driven: A/B/C/D selects an option, Enter confirms, → moves on
// once a resolution has been saved (there is no "skip ahead" — the queue
// always shows the next unresolved task).
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError, type ResolutionCommand, type ReviewTask } from '../../api/contracts';
import { useRuntime } from '../../app/providers';
import { Evidence } from '../../shared/Evidence';
import { Card, CardHeader, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Button } from '../../components/ui/button';

export function HitlQueue() {
  const { api, scope } = useRuntime();
  const client = useQueryClient();
  const key = [scope, 'review-queue'] as const;
  const [notice, setNotice] = useState('');
  const query = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => api.reviewQueue(signal),
    refetchOnWindowFocus: true,
    refetchInterval: q => q.state.error ? false : 15000,
    refetchIntervalInBackground: false
  });

  async function reconcile(taskId: string, message: string) {
    await client.cancelQueries({ queryKey: key });
    client.setQueryData<ReviewTask[]>(key, old => old?.filter(t => t.id !== taskId));
    setNotice(message);
    await client.invalidateQueries({ queryKey: key });
  }

  const queueLength = query.data?.length ?? 0;
  const task = query.data?.[0];

  return (
    <section className="mx-auto max-w-4xl space-y-4" data-testid="hitl-queue">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Bubble review</h1>
          <p className="text-sm text-muted-foreground">Only isolated, approved-for-review evidence appears here.</p>
        </div>
        {query.isSuccess && (
          <Badge variant={queueLength > 0 ? 'secondary' : 'default'} data-testid="queue-count">
            {queueLength} pending
          </Badge>
        )}
      </header>
      <p role="status" aria-live="polite" className="sr-only" data-testid="hitl-notice">{notice}</p>

      {query.isPending && (
        <Card data-testid="hitl-loading" aria-busy="true">
          <CardHeader><Skeleton className="h-6 w-40" /></CardHeader>
          <CardContent className="grid gap-6 lg:grid-cols-2">
            <Skeleton className="h-64 w-full" />
            <div className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-24 w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {query.isError && (
        <Alert variant="destructive" data-testid="hitl-error">
          <AlertTitle>The queue could not be refreshed</AlertTitle>
          <AlertDescription className="space-y-3">
            <p>Resolution is paused until it reconnects.</p>
            <Button onClick={() => void query.refetch()}>Reconnect</Button>
          </AlertDescription>
        </Alert>
      )}

      {query.isSuccess && !task && (
        <Card data-testid="hitl-empty">
          <CardContent className="py-10 text-center text-muted-foreground">
            No tasks currently require your review.
          </CardContent>
        </Card>
      )}

      {task && (
        <ResolutionForm key={`${task.id}:${task.revision}`} task={task}
          blocked={query.isError}
          onRemoved={message => reconcile(task.id, message)} />
      )}
    </section>
  );
}

function ResolutionForm({ task, blocked, onRemoved }: {
  task: ReviewTask;
  blocked: boolean;
  onRemoved: (message: string) => Promise<void>;
}) {
  const { api } = useRuntime();
  const [ready, setReady] = useState(false);
  const [choice, setChoice] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const heading = useRef<HTMLHeadingElement>(null);
  const locked = useRef(false);
  const last = useRef<{ payload: string; key: string } | null>(null);
  const mutation = useMutation({
    mutationFn: (command: ResolutionCommand) => api.resolveTask(task.id, command),
    retry: false
  });
  useEffect(() => { heading.current?.focus(); }, []);

  const changesSuggestion = choice !== task.suggestedCode;
  const valid = task.choices.some(option => option.code === choice) &&
    (!changesSuggestion || Boolean(reason.trim()));

  async function submit() {
    if (locked.current || blocked || !ready || !valid) return;
    locked.current = true;
    setError('');
    const payload = JSON.stringify([task.id, task.revision, choice, reason.trim()]);
    if (last.current?.payload !== payload) last.current = { payload, key: crypto.randomUUID() };
    try {
      await mutation.mutateAsync({
        expectedRevision: task.revision,
        decisionCode: choice,
        reason: reason.trim(),
        idempotencyKey: last.current.key
      });
      await onRemoved('Resolution saved. Next task loaded.');
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 409) {
        await onRemoved('This task changed or was resolved. Its stale version was removed and the queue refreshed.');
      } else {
        setError('Resolution was not confirmed. Your selection is preserved; reconnect and retry the same decision.');
      }
    } finally {
      locked.current = false;
    }
  }

  // Keyboard-driven review: letter keys select an option, Enter confirms.
  // Ignored while typing in the reason field so letters there aren't hijacked.
  function onKeyDown(event: React.KeyboardEvent) {
    const target = event.target as HTMLElement;
    const typingInReason = target.tagName === 'TEXTAREA';
    if (!typingInReason) {
      const upper = event.key.toUpperCase();
      const match = task.choices.find(o => o.code.toUpperCase() === upper);
      if (match) {
        event.preventDefault();
        setChoice(match.code);
        return;
      }
    }
    if (event.key === 'Enter' && !event.shiftKey && (typingInReason ? event.metaKey || event.ctrlKey : true)) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <Card data-testid="resolution-form" onKeyDown={onKeyDown}>
      <CardContent className="grid gap-6 pt-6 lg:grid-cols-2">
        <div>
          <h2 ref={heading} tabIndex={-1} className="mb-3 font-semibold outline-none" data-testid="crop-heading">
            Question {task.cropId}
          </h2>
          <Evidence key={`admin:${task.cropId}`} cropId={task.cropId} audience="admin" onReady={setReady} />
        </div>
        <form className="space-y-4" onSubmit={event => { event.preventDefault(); void submit(); }}>
          <div>
            <p className="font-medium">{task.kind === 'ambiguous' ? 'Ambiguous bubble reading' : 'Diagnosis requires human review'}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Inspect the evidence before choosing a resolution. No option is selected automatically.
              Press <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs">A</kbd>–<kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs">D</kbd> to choose, <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-xs">Enter</kbd> to confirm.
            </p>
          </div>
          <fieldset disabled={mutation.isPending || blocked} className="space-y-1">
            <legend className="mb-2 font-medium">Resolution</legend>
            {task.choices.map(option => (
              <label key={option.code}
                className={`flex min-h-11 items-center gap-3 rounded-lg border px-3 transition-colors ${choice === option.code ? 'border-primary bg-accent' : 'border-border'}`}>
                <input type="radio" name={`resolution-${task.id}`} value={option.code}
                  checked={choice === option.code} onChange={() => setChoice(option.code)}
                  data-testid={`option-${option.code}`} />
                <span className="font-mono text-xs text-muted-foreground">{option.code}</span>
                <span>{option.label}{option.code === task.suggestedCode ? ' — suggested reading' : ''}</span>
              </label>
            ))}
          </fieldset>
          <label className="block">
            <span className="block font-medium">Reason {changesSuggestion ? '(required)' : '(optional)'}</span>
            <textarea value={reason} rows={3} disabled={mutation.isPending || blocked}
              onChange={event => setReason(event.target.value)}
              data-testid="reason-input"
              className="mt-2 w-full rounded-lg border border-input bg-transparent p-3 text-sm" />
          </label>
          <p className="text-xs text-muted-foreground">Do not enter names or other identifying information.</p>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <Button type="submit" data-testid="submit-resolution"
            disabled={!ready || !valid || blocked || mutation.isPending}>
            {mutation.isPending ? 'Saving resolution…' : 'Save resolution and continue'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
