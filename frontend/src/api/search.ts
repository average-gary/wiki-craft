import { apiGet, apiPost } from './client';
import type {
  SearchQuery,
  SearchResponse,
  SearchResult,
  ChunkContext,
  DocumentType,
} from '@/types/api';

export async function search(query: SearchQuery): Promise<SearchResponse> {
  return apiPost<SearchResponse>('/search', query);
}

export async function searchSimple(
  q: string,
  limit = 10,
  minScore = 0,
  documentTypes?: DocumentType[]
): Promise<SearchResponse> {
  const params: Record<string, string | number | boolean | undefined> = {
    q,
    limit,
    min_score: minScore,
  };
  
  // Handle document types as multiple query params
  if (documentTypes && documentTypes.length > 0) {
    // For multiple values, we need to construct the URL manually
    const url = new URL('/api/v1/search', window.location.origin);
    url.searchParams.append('q', q);
    url.searchParams.append('limit', String(limit));
    url.searchParams.append('min_score', String(minScore));
    documentTypes.forEach(type => {
      url.searchParams.append('document_type', type);
    });
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  return apiGet<SearchResponse>('/search', params);
}

export async function searchSimilar(chunkId: string, limit = 10): Promise<SearchResult[]> {
  return apiGet<SearchResult[]>(`/search/similar/${chunkId}`, { limit });
}

export async function getChunkContext(chunkId: string, window = 2): Promise<ChunkContext> {
  return apiGet<ChunkContext>(`/search/context/${chunkId}`, { window });
}
