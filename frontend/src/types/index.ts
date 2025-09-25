// Type definitions for the RAG BCI Literature Scout

export interface QueryRequest {
  query: string;
  date_range?: {
    start: string;
    end: string;
  };
  sources?: string[];
  max_results?: number;
}

export interface PaperMetadata {
  id: string;
  title: string;
  authors: string[];
  year: number;
  abstract: string;
  url: string;
  source: string;
  doi?: string;
  citation_count?: number;
}

export interface Claim {
  id?: string;
  text: string;
  confidence: number;
  evidence: string[];
  supporting_papers: string[];
}

export interface TrendSummary {
  summary: string;
  trend_summary: string;
  claims: Claim[];
  papers: PaperMetadata[];
  timeline?: Record<string, number>;
  reproducibility_snapshot: Record<string, any>;
}

export interface QueryResponse {
  query: string;
  summary: TrendSummary;
  processing_time: number;
  timestamp: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  status_code: number;
}
