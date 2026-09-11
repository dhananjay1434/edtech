// features/admin/AdminConsole.tsx — the admin setup/operations hub.
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import { RosterImportPanel } from './RosterImportPanel';
import { ExamSetupPanel } from './ExamSetupPanel';
import { BatchUploadPanel } from './BatchUploadPanel';
import { IdentityQueuePanel } from './IdentityQueuePanel';
import { IntegerAnswersPanel } from './IntegerAnswersPanel';
import { ExceptionsPanel } from './ExceptionsPanel';

export function AdminConsole() {
  return (
    <section className="space-y-6" data-testid="admin-console">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Admin console</h1>
        <p className="text-sm text-muted-foreground">Set up the class, run the batch, and resolve what needs a human.</p>
      </header>
      <Tabs defaultValue="roster">
        <TabsList>
          <TabsTrigger value="roster">Roster</TabsTrigger>
          <TabsTrigger value="exam">Exam setup</TabsTrigger>
          <TabsTrigger value="batch">Batch upload</TabsTrigger>
          <TabsTrigger value="identity">Identity</TabsTrigger>
          <TabsTrigger value="integers">Integer answers</TabsTrigger>
          <TabsTrigger value="exceptions">Exceptions</TabsTrigger>
        </TabsList>
        <TabsContent value="roster"><RosterImportPanel /></TabsContent>
        <TabsContent value="exam"><ExamSetupPanel /></TabsContent>
        <TabsContent value="batch"><BatchUploadPanel /></TabsContent>
        <TabsContent value="identity"><IdentityQueuePanel /></TabsContent>
        <TabsContent value="integers"><IntegerAnswersPanel /></TabsContent>
        <TabsContent value="exceptions"><ExceptionsPanel /></TabsContent>
      </Tabs>
    </section>
  );
}
