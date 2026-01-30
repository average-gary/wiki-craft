import { apiGet, apiPost } from './client';
import type {
  WikiGenerateRequest,
  WikiGenerateResponse,
  WikiTopicsResponse,
  WikiSectionResponse,
  CompareSourcesResponse,
} from '@/types/api';

export async function generateWiki(request: WikiGenerateRequest): Promise<WikiGenerateResponse> {
  return apiPost<WikiGenerateResponse>('/wiki/generate', request);
}

export async function generateWikiSimple(
  query: string,
  maxSources = 10,
  format: 'markdown' | 'html' | 'json' | 'text' = 'html',
  includeSources = true
): Promise<WikiGenerateResponse> {
  return apiGet<WikiGenerateResponse>('/wiki/generate', {
    q: query,
    max_sources: maxSources,
    format,
    include_sources: includeSources,
  });
}

export async function getWikiTopics(limit = 20): Promise<WikiTopicsResponse> {
  return apiGet<WikiTopicsResponse>('/wiki/topics', { limit });
}

export async function generateWikiSection(
  topic: string,
  context?: string,
  maxSources = 5
): Promise<WikiSectionResponse> {
  const params: Record<string, string | number | undefined> = {
    topic,
    max_sources: maxSources,
  };
  
  if (context) {
    params.context = context;
  }
  
  return apiPost<WikiSectionResponse>('/wiki/section', undefined);
}

export async function compareSources(
  query: string,
  maxPerSource = 3
): Promise<CompareSourcesResponse> {
  return apiPost<CompareSourcesResponse>('/wiki/compare', { query, max_per_source: maxPerSource });
}
