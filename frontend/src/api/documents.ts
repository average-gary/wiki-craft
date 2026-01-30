import { apiGet, apiDelete, apiUpload, apiUploadMultiple } from './client';
import type {
  DocumentListResponse,
  DocumentDetail,
  DocumentChunksResponse,
  DocumentTextResponse,
  IngestResponse,
  StatsResponse,
} from '@/types/api';

export async function getDocuments(offset = 0, limit = 50): Promise<DocumentListResponse> {
  return apiGet<DocumentListResponse>('/documents', { offset, limit });
}

export async function getDocument(documentId: string): Promise<DocumentDetail> {
  return apiGet<DocumentDetail>(`/documents/${documentId}`);
}

export async function getDocumentChunks(
  documentId: string,
  offset = 0,
  limit = 50
): Promise<DocumentChunksResponse> {
  return apiGet<DocumentChunksResponse>(`/documents/${documentId}/chunks`, { offset, limit });
}

export async function getDocumentText(documentId: string): Promise<DocumentTextResponse> {
  return apiGet<DocumentTextResponse>(`/documents/${documentId}/text`);
}

export async function deleteDocument(documentId: string): Promise<{ status: string; document_id: string; chunks_deleted: number }> {
  return apiDelete(`/documents/${documentId}`);
}

export async function uploadDocument(file: File, metadata?: Record<string, unknown>): Promise<IngestResponse> {
  return apiUpload<IngestResponse>('/ingest/file', file, metadata);
}

export async function uploadDocuments(files: File[]): Promise<IngestResponse[]> {
  return apiUploadMultiple<IngestResponse[]>('/ingest/batch', files);
}

export async function ingestUrl(url: string, metadata?: Record<string, unknown>): Promise<IngestResponse> {
  const { apiPost } = await import('./client');
  return apiPost<IngestResponse>('/ingest/url', {
    url,
    custom_metadata: metadata || {},
  });
}

export async function getStats(): Promise<StatsResponse> {
  return apiGet<StatsResponse>('/stats');
}

export async function getChunk(chunkId: string): Promise<{
  chunk_id: string;
  text: string;
  metadata: {
    document_id: string;
    document_title: string | null;
    source_path: string;
    page_number: number | null;
    section_hierarchy: string[];
    chunk_index: number;
    total_chunks: number;
    content_type: string;
  };
}> {
  return apiGet(`/chunks/${chunkId}`);
}
