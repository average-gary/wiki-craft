import { useQuery, useMutation } from '@tanstack/react-query';
import { generateWiki, generateWikiSimple, getWikiTopics } from '@/api/wiki';
import type { WikiGenerateRequest } from '@/types/api';

export function useGenerateWiki() {
  return useMutation({
    mutationFn: (request: WikiGenerateRequest) => generateWiki(request),
  });
}

export function useGenerateWikiSimple(
  query: string | null,
  maxSources = 10,
  format: 'markdown' | 'html' | 'json' | 'text' = 'html',
  includeSources = true
) {
  return useQuery({
    queryKey: ['wiki', query, maxSources, format, includeSources],
    queryFn: () => generateWikiSimple(query!, maxSources, format, includeSources),
    enabled: !!query,
  });
}

export function useWikiTopics(limit = 20) {
  return useQuery({
    queryKey: ['wikiTopics', limit],
    queryFn: () => getWikiTopics(limit),
  });
}
