import { useState } from 'react';
import { SearchBar } from '@/components/search/SearchBar';
import { SearchFilters } from '@/components/search/SearchFilters';
import { SearchResults } from '@/components/search/SearchResults';
import { NoSearchResults } from '@/components/common/EmptyState';
import { SearchResultSkeleton } from '@/components/common/LoadingState';
import { useSearchMutation } from '@/hooks/useSearch';
import type { DocumentType, SearchResponse } from '@/types/api';

export function SearchPage() {
  const [selectedTypes, setSelectedTypes] = useState<DocumentType[]>([]);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  
  const searchMutation = useSearchMutation();

  const handleSearch = (query: string) => {
    setLastQuery(query);
    searchMutation.mutate(
      {
        query,
        limit: 20,
        document_types: selectedTypes.length > 0 ? selectedTypes : undefined,
      },
      {
        onSuccess: (data) => setResults(data),
      }
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Search</h1>
        <p className="text-muted-foreground mt-1">
          Search across your entire knowledge base using natural language.
        </p>
      </div>

      <div className="space-y-4">
        <SearchBar
          onSearch={handleSearch}
          isLoading={searchMutation.isPending}
          placeholder="Ask a question or search for a topic..."
        />
        <SearchFilters
          selectedTypes={selectedTypes}
          onTypesChange={setSelectedTypes}
        />
      </div>

      <div className="min-h-[300px]">
        {searchMutation.isPending ? (
          <div className="space-y-4">
            <SearchResultSkeleton />
            <SearchResultSkeleton />
            <SearchResultSkeleton />
          </div>
        ) : results ? (
          results.results.length > 0 ? (
            <SearchResults
              results={results.results}
              searchTime={results.search_time_ms}
            />
          ) : (
            <NoSearchResults query={lastQuery} />
          )
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-muted-foreground">
              Enter a search query to find relevant information in your knowledge base.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
