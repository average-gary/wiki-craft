import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDocuments,
  getDocument,
  getDocumentChunks,
  getDocumentText,
  deleteDocument,
  uploadDocument,
  uploadDocuments,
} from '@/api/documents';

export function useDocuments(offset = 0, limit = 50) {
  return useQuery({
    queryKey: ['documents', offset, limit],
    queryFn: () => getDocuments(offset, limit),
  });
}

export function useDocument(documentId: string | undefined) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: () => getDocument(documentId!),
    enabled: !!documentId,
  });
}

export function useDocumentChunks(documentId: string | undefined, offset = 0, limit = 50) {
  return useQuery({
    queryKey: ['documentChunks', documentId, offset, limit],
    queryFn: () => getDocumentChunks(documentId!, offset, limit),
    enabled: !!documentId,
  });
}

export function useDocumentText(documentId: string | undefined) {
  return useQuery({
    queryKey: ['documentText', documentId],
    queryFn: () => getDocumentText(documentId!),
    enabled: !!documentId,
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata?: Record<string, unknown> }) =>
      uploadDocument(file, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useUploadDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (files: File[]) => uploadDocuments(files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
