// Document Types
export type DocumentType = 'pdf' | 'docx' | 'xlsx' | 'markdown' | 'text' | 'html' | 'epub' | 'unknown';

export type ContentType = 'paragraph' | 'heading' | 'list' | 'table' | 'code' | 'quote' | 'image_caption' | 'footnote' | 'unknown';

// Document Models
export interface DocumentInfo {
  document_id: string;
  source_path: string;
  document_title: string | null;
  document_type: DocumentType;
  total_chunks: number;
  ingested_at: string;
}

export interface DocumentDetail {
  document_id: string;
  source_path: string;
  document_title: string | null;
  document_type: string;
  total_chunks: number;
  ingested_at: string;
  sections: SectionInfo[];
}

export interface SectionInfo {
  hierarchy: string[];
  page_number: number | null;
}

export interface DocumentChunk {
  chunk_id: string;
  text: string;
  chunk_index: number;
  page_number: number | null;
  section: string | null;
}

export interface DocumentChunksResponse {
  document_id: string;
  chunks: DocumentChunk[];
  total: number;
  offset: number;
  limit: number;
}

export interface DocumentTextResponse {
  document_id: string;
  document_title: string | null;
  text: string;
  word_count: number;
  chunk_count: number;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
  offset: number;
  limit: number;
}

// Ingest Models
export interface IngestResponse {
  document_id: string;
  filename: string;
  document_type: DocumentType;
  chunks_created: number;
  status: string;
  errors: string[];
}

// Search Models
export interface SearchQuery {
  query: string;
  limit?: number;
  min_score?: number;
  document_ids?: string[];
  document_types?: DocumentType[];
  include_embeddings?: boolean;
}

export interface ChunkMetadata {
  document_id: string;
  source_path: string;
  source_hash: string;
  document_title: string | null;
  document_type: DocumentType;
  page_number: number | null;
  section_hierarchy: string[];
  paragraph_index: number;
  chunk_index: number;
  total_chunks: number;
  content_type: ContentType;
  char_start: number;
  char_end: number;
  ingested_at: string;
  document_version: string | null;
}

export interface SearchResult {
  chunk_id: string;
  text: string;
  score: number;
  metadata: ChunkMetadata;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

export interface ChunkContext {
  target_chunk: {
    id: string;
    text: string;
    index: number;
  };
  context: {
    id: string;
    text: string;
    index: number;
    is_target: boolean;
  }[];
  document_id: string;
  document_title: string | null;
}

// Wiki Models
export interface WikiSource {
  chunk_id: string;
  document_id: string;
  document_title: string | null;
  source_path: string;
  page_number: number | null;
  section: string | null;
  relevance_score: number;
  excerpt: string;
}

export interface WikiSection {
  heading: string;
  content: string;
  sources: WikiSource[];
  confidence: number;
  subsections: WikiSection[];
}

export interface WikiEntry {
  entry_id: string;
  title: string;
  summary: string;
  sections: WikiSection[];
  all_sources: WikiSource[];
  generated_at: string;
  query: string;
}

export interface WikiGenerateRequest {
  query: string;
  max_sources?: number;
  output_format?: 'markdown' | 'html' | 'json' | 'text';
  include_sources?: boolean;
}

export interface WikiGenerateResponse {
  entry: WikiEntry;
  content: string;
  format: string;
}

export interface WikiTopicsResponse {
  topics: string[];
  total: number;
}

export interface WikiSectionResponse {
  heading: string;
  content: string;
  confidence: number;
  sources: WikiSource[];
}

export interface CompareSourcesResponse {
  query: string;
  sources: {
    document_id: string;
    document_title: string;
    source_path: string;
    excerpts: {
      text: string;
      score: number;
      page_number: number | null;
      section: string | null;
    }[];
  }[];
  source_count: number;
}

// Stats Models
export interface StatsResponse {
  total_documents: number;
  total_chunks: number;
  documents_by_type: Record<string, number>;
  avg_chunks_per_document: number;
}

// Health Check
export interface HealthResponse {
  status: string;
  version: string;
}
