import { useQuery } from '@tanstack/react-query';
import { getStats } from '@/api/documents';
import { healthCheck } from '@/api/client';

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  });
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
  });
}
