import { useQuery, useMutation } from '@tanstack/react-query';
import { search, searchSimple, searchSimilar, getChunkContext } from '@/api/search';
import type { SearchQuery, DocumentType } from '@/types/api';

export function useSearch(query: SearchQuery | null) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () => search(query!),
    enabled: !!query && !!query.query,
  });
}

export function useSearchSimple(
  q: string | null,
  limit = 10,
  minScore = 0,
  documentTypes?: DocumentType[]
) {
  return useQuery({
    queryKey: ['search', q, limit, minScore, documentTypes],
    queryFn: () => searchSimple(q!, limit, minScore, documentTypes),
    enabled: !!q,
  });
}

export function useSearchMutation() {
  return useMutation({
    mutationFn: (query: SearchQuery) => search(query),
  });
}

export function useSearchSimilar(chunkId: string | undefined, limit = 10) {
  return useQuery({
    queryKey: ['searchSimilar', chunkId, limit],
    queryFn: () => searchSimilar(chunkId!, limit),
    enabled: !!chunkId,
  });
}

export function useChunkContext(chunkId: string | undefined, window = 2) {
  return useQuery({
    queryKey: ['chunkContext', chunkId, window],
    queryFn: () => getChunkContext(chunkId!, window),
    enabled: !!chunkId,
  });
}
