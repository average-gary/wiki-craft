import { useState } from 'react';
import { useDocument, useDocumentChunks, useDocumentText } from '@/hooks/useDocuments';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { LoadingSpinner } from '@/components/common/LoadingState';
import { formatDate, getDocumentTypeIcon, truncateText } from '@/lib/utils';
import { FileText, Copy, ChevronDown, ChevronUp } from 'lucide-react';

interface DocumentDetailProps {
  documentId: string;
}

export function DocumentDetail({ documentId }: DocumentDetailProps) {
  const { data: doc, isLoading: docLoading } = useDocument(documentId);
  const { data: chunks, isLoading: chunksLoading } = useDocumentChunks(documentId, 0, 20);
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());
  const [showFullText, setShowFullText] = useState(false);
  const { data: fullText, isLoading: textLoading } = useDocumentText(
    showFullText ? documentId : undefined
  );

  if (docLoading) {
    return <LoadingSpinner className="py-8" />;
  }

  if (!doc) {
    return <div className="text-center py-8 text-muted-foreground">Document not found</div>;
  }

  const toggleChunk = (index: number) => {
    setExpandedChunks(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="text-3xl">{getDocumentTypeIcon(doc.document_type)}</div>
        <div className="flex-1">
          <h2 className="text-xl font-semibold">
            {doc.document_title || doc.source_path.split('/').pop()}
          </h2>
          <p className="text-sm text-muted-foreground">{doc.source_path}</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">{doc.document_type.toUpperCase()}</Badge>
            <span className="text-sm text-muted-foreground">
              {doc.total_chunks} chunks
            </span>
            <span className="text-sm text-muted-foreground">
              Ingested {formatDate(doc.ingested_at)}
            </span>
          </div>
        </div>
      </div>

      <Separator />

      {/* Tabs */}
      <Tabs defaultValue="chunks">
        <TabsList>
          <TabsTrigger value="chunks">Chunks ({doc.total_chunks})</TabsTrigger>
          <TabsTrigger value="sections">Sections</TabsTrigger>
          <TabsTrigger value="fulltext">Full Text</TabsTrigger>
        </TabsList>

        <TabsContent value="chunks" className="mt-4">
          {chunksLoading ? (
            <LoadingSpinner className="py-4" />
          ) : chunks?.chunks.length ? (
            <div className="space-y-2">
              {chunks.chunks.map((chunk, idx) => (
                <div
                  key={chunk.chunk_id}
                  className="border rounded-lg p-3 bg-muted/30"
                >
                  <div
                    className="flex items-start gap-2 cursor-pointer"
                    onClick={() => toggleChunk(idx)}
                  >
                    <span className="text-xs text-muted-foreground font-mono min-w-[3rem]">
                      #{chunk.chunk_index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">
                        {expandedChunks.has(idx)
                          ? chunk.text
                          : truncateText(chunk.text, 150)}
                      </p>
                      {chunk.section && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {chunk.section}
                          {chunk.page_number && ` • Page ${chunk.page_number}`}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation();
                        copyToClipboard(chunk.text);
                      }}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                    {chunk.text.length > 150 && (
                      expandedChunks.has(idx) ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )
                    )}
                  </div>
                </div>
              ))}
              {chunks.total > chunks.chunks.length && (
                <p className="text-sm text-muted-foreground text-center py-2">
                  Showing {chunks.chunks.length} of {chunks.total} chunks
                </p>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">No chunks found</p>
          )}
        </TabsContent>

        <TabsContent value="sections" className="mt-4">
          {doc.sections?.length ? (
            <div className="space-y-2">
              {doc.sections.map((section, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 rounded border bg-muted/30">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{section.hierarchy.join(' > ')}</span>
                  {section.page_number && (
                    <Badge variant="outline" className="ml-auto text-xs">
                      Page {section.page_number}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">No sections found</p>
          )}
        </TabsContent>

        <TabsContent value="fulltext" className="mt-4">
          {!showFullText ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">
                Load the full reconstructed document text
              </p>
              <Button onClick={() => setShowFullText(true)}>
                Load Full Text
              </Button>
            </div>
          ) : textLoading ? (
            <LoadingSpinner className="py-8" />
          ) : fullText ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {fullText.word_count.toLocaleString()} words
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(fullText.text)}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy All
                </Button>
              </div>
              <div className="border rounded-lg p-4 bg-muted/30 max-h-96 overflow-y-auto">
                <pre className="text-sm whitespace-pre-wrap font-sans">
                  {fullText.text}
                </pre>
              </div>
            </div>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}
