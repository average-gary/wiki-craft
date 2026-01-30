import { Copy, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { downloadFile } from '@/lib/utils';
import type { WikiGenerateResponse, WikiSource } from '@/types/api';

interface WikiContentProps {
  data: WikiGenerateResponse;
}

export function WikiContent({ data }: WikiContentProps) {
  const { entry, content } = data;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(content);
  };

  const downloadHtml = () => {
    const filename = entry.title.replace(/\s+/g, '-').toLowerCase() + '.html';
    downloadFile(content, filename, 'text/html');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">{entry.title}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Generated from {entry.all_sources.length} sources
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={copyToClipboard}>
            <Copy className="h-4 w-4 mr-2" />
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={downloadHtml}>
            <Download className="h-4 w-4 mr-2" />
            Download HTML
          </Button>
        </div>
      </div>

      <Separator />

      <Tabs defaultValue="preview" className="w-full">
        <TabsList>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="sources">Sources ({entry.all_sources.length})</TabsTrigger>
          <TabsTrigger value="raw">Raw HTML</TabsTrigger>
        </TabsList>

        <TabsContent value="preview" className="mt-4">
          <Card>
            <CardContent className="p-6">
              <div
                className="prose-wiki"
                dangerouslySetInnerHTML={{ __html: content }}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sources" className="mt-4">
          <SourcesList sources={entry.all_sources} />
        </TabsContent>

        <TabsContent value="raw" className="mt-4">
          <Card>
            <CardContent className="p-4">
              <pre className="text-sm overflow-x-auto whitespace-pre-wrap bg-muted p-4 rounded-lg">
                {content}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface SourcesListProps {
  sources: WikiSource[];
}

function SourcesList({ sources }: SourcesListProps) {
  if (sources.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-8">
        No sources available
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {sources.map((source, index) => (
        <Card key={source.chunk_id}>
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between">
              <CardTitle className="text-base font-medium">
                {index + 1}. {source.document_title || source.source_path.split('/').pop()}
              </CardTitle>
              <Badge variant="secondary">
                {Math.round(source.relevance_score * 100)}% match
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-sm text-muted-foreground mb-2">
              {source.page_number && <span>Page {source.page_number}</span>}
              {source.section && (
                <>
                  {source.page_number && ' • '}
                  <span>{source.section}</span>
                </>
              )}
            </div>
            <p className="text-sm bg-muted/50 p-3 rounded-lg italic">
              "{source.excerpt}"
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
