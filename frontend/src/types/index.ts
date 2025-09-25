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

// Sprint 5 Types for Advanced Features

export interface TimelineData {
  papers_per_year: Record<number, number>;
  keyword_trends: Record<string, Array<{
    year: number;
    count: number;
  }>>;
  total_papers: number;
  year_range: {
    min: number;
    max: number;
  };
}

export interface ClusterPoint {
  id: string;
  x: number;
  y: number;
  cluster_id: number;
  title: string;
  year: number;
  keywords: string[];
  citation_count?: number;
}

export interface ClusterData {
  points: ClusterPoint[];
  clusters: Record<number, {
    size: number;
    top_keywords: string[];
    year_range: {
      min: number;
      max: number;
    };
  }>;
  algorithm: string;
  parameters: Record<string, any>;
  message?: string;
}

export interface SourceInfo {
  name: string;
  description: string;
  last_updated: string;
  paper_count: number;
  coverage: {
    year_range: {
      min: number;
      max: number;
    };
    total_citations: number;
    avg_citations: number;
  };
}

export interface PromptTransparency {
  system_prompt: string;
  user_prompt_template: string;
  parameters: Record<string, any>;
  model_info: Record<string, string>;
}

export interface ReproducibilityInfo {
  snapshot_id: string;
  timestamp: string;
  query: string;
  parameters: Record<string, any>;
  data_version: string;
  model_version: string;
}
