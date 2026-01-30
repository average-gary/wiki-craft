import { useState } from 'react';
import { WikiGenerator } from '@/components/wiki/WikiGenerator';
import { WikiContent } from '@/components/wiki/WikiContent';
import { NoWikiContent } from '@/components/common/EmptyState';
import { WikiContentSkeleton } from '@/components/common/LoadingState';
import { useGenerateWiki } from '@/hooks/useWiki';
import { Card, CardContent } from '@/components/ui/card';
import type { WikiGenerateResponse } from '@/types/api';

export function WikiPage() {
  const [wikiData, setWikiData] = useState<WikiGenerateResponse | null>(null);
  const generateMutation = useGenerateWiki();

  const handleGenerate = (query: string, maxSources: number, includeSources: boolean) => {
    generateMutation.mutate(
      {
        query,
        max_sources: maxSources,
        output_format: 'html',
        include_sources: includeSources,
      },
      {
        onSuccess: (data) => setWikiData(data),
      }
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Generate Wiki</h1>
        <p className="text-muted-foreground mt-1">
          Create wiki-style entries with automatic source citations from your knowledge base.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <WikiGenerator
            onGenerate={handleGenerate}
            isLoading={generateMutation.isPending}
          />
        </CardContent>
      </Card>

      <div className="min-h-[400px]">
        {generateMutation.isPending ? (
          <Card>
            <CardContent className="pt-6">
              <WikiContentSkeleton />
            </CardContent>
          </Card>
        ) : generateMutation.isError ? (
          <Card>
            <CardContent className="py-8 text-center">
              <p className="text-destructive">
                Failed to generate wiki entry. Please try again.
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                {generateMutation.error?.message}
              </p>
            </CardContent>
          </Card>
        ) : wikiData ? (
          <WikiContent data={wikiData} />
        ) : (
          <NoWikiContent />
        )}
      </div>
    </div>
  );
}
