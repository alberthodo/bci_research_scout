// API service for communicating with the backend

import type { 
  QueryRequest, QueryResponse, ApiError, 
  TimelineData, ClusterData, SourceInfo 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async queryLiterature(request: QueryRequest): Promise<QueryResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.error || 'Failed to query literature');
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (!response.ok) {
        throw new Error('Health check failed');
      }
      return await response.json();
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }

  // Sprint 5 API Methods

  async getTimelineData(): Promise<TimelineData> {
    try {
      const response = await fetch(`${this.baseUrl}/timeline`);
      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.error || 'Failed to get timeline data');
      }
      return await response.json();
    } catch (error) {
      console.error('Timeline data error:', error);
      throw error;
    }
  }

  async getClusterData(): Promise<ClusterData> {
    try {
      const response = await fetch(`${this.baseUrl}/clusters`);
      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.error || 'Failed to get cluster data');
      }
      return await response.json();
    } catch (error) {
      console.error('Cluster data error:', error);
      throw error;
    }
  }

  async getSourcesInfo(): Promise<Record<string, SourceInfo>> {
    try {
      const response = await fetch(`${this.baseUrl}/sources`);
      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.error || 'Failed to get sources info');
      }
      return await response.json();
    } catch (error) {
      console.error('Sources info error:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
