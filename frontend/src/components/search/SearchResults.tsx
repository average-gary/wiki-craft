import { useState } from 'react';
import { ExternalLink, Copy, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useChunkContext } from '@/hooks/useSearch';
import { getDocumentTypeIcon, truncateText } from '@/lib/utils';
import { LoadingSpinner } from '@/components/common/LoadingState';
import type { SearchResult } from '@/types/api';

interface SearchResultsProps {
  results: SearchResult[];
  searchTime?: number;
}

export function SearchResults({ results, searchTime }: SearchResultsProps) {
  const [contextChunkId, setContextChunkId] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      {searchTime !== undefined && (
        <p className="text-sm text-muted-foreground">
          Found {results.length} results in {searchTime.toFixed(0)}ms
        </p>
      )}

      <div className="space-y-3">
        {results.map((result) => (
          <SearchResultCard
            key={result.chunk_id}
            result={result}
            onViewContext={() => setContextChunkId(result.chunk_id)}
          />
        ))}
      </div>

      <Dialog open={!!contextChunkId} onOpenChange={() => setContextChunkId(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Chunk Context</DialogTitle>
          </DialogHeader>
          {contextChunkId && <ChunkContextView chunkId={contextChunkId} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
  onViewContext: () => void;
}

function SearchResultCard({ result, onViewContext }: SearchResultCardProps) {
  const scorePercent = Math.round(result.score * 100);
  const scoreColor =
    scorePercent >= 80
      ? 'text-green-500'
      : scorePercent >= 60
      ? 'text-yellow-500'
      : 'text-orange-500';

  const copyText = () => {
    navigator.clipboard.writeText(result.text);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="text-xl">
            {getDocumentTypeIcon(result.metadata.document_type)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-sm font-bold ${scoreColor}`}>
                {scorePercent}%
              </span>
              <span className="font-medium truncate">
                {result.metadata.document_title || result.metadata.source_path.split('/').pop()}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
              {result.metadata.page_number && (
                <span>Page {result.metadata.page_number}</span>
              )}
              {result.metadata.section_hierarchy.length > 0 && (
                <span className="truncate">
                  {result.metadata.section_hierarchy.join(' > ')}
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {truncateText(result.text, 300)}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <Button variant="outline" size="sm" onClick={onViewContext}>
                <ExternalLink className="h-3 w-3 mr-1" />
                View Context
              </Button>
              <Button variant="ghost" size="sm" onClick={copyText}>
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ChunkContextView({ chunkId }: { chunkId: string }) {
  const { data, isLoading, error } = useChunkContext(chunkId, 3);

  if (isLoading) return <LoadingSpinner className="py-8" />;
  if (error) return <p className="text-destructive">Failed to load context</p>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        Document: {data.document_title || 'Untitled'}
      </div>
      <div className="space-y-2">
        {data.context.map((chunk) => (
          <div
            key={chunk.id}
            className={`p-3 rounded-lg border ${
              chunk.is_target
                ? 'bg-primary/10 border-primary'
                : 'bg-muted/30'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-muted-foreground">
                #{chunk.index + 1}
              </span>
              {chunk.is_target && (
                <Badge variant="default" className="text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  Match
                </Badge>
              )}
            </div>
            <p className="text-sm">{chunk.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
