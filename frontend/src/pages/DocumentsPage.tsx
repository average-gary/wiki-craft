import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DocumentList } from '@/components/documents/DocumentList';
import { UploadZone } from '@/components/documents/UploadZone';

export function DocumentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="text-muted-foreground mt-1">
          Upload and manage your documents in the knowledge base.
        </p>
      </div>

      <Tabs defaultValue="browse" className="w-full">
        <TabsList>
          <TabsTrigger value="browse">Browse Documents</TabsTrigger>
          <TabsTrigger value="upload">Upload New</TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="mt-6">
          <DocumentList />
        </TabsContent>

        <TabsContent value="upload" className="mt-6">
          <div className="max-w-2xl">
            <UploadZone />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
